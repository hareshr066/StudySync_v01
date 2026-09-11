"""Study group management service."""

import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.db.mongodb import get_database


class GroupService:
    """Handles study group CRUD and membership operations."""

    def __init__(self):
        self.db = get_database()

    def create_group(self, owner_id: str, name: str, description: str = "") -> Dict[str, Any]:
        """Create a new study group."""
        now = datetime.now(timezone.utc)
        doc = {
            "name": name.strip(),
            "description": description.strip(),
            "owner_id": owner_id,
            "member_count": 1,
            "invite_token": None,
            "created_at": now,
            "updated_at": now,
        }
        result = self.db.study_groups.insert_one(doc)
        group_id = str(result.inserted_id)

        self.db.study_group_members.insert_one({
            "group_id": group_id,
            "user_id": owner_id,
            "role": "owner",
            "joined_at": now,
        })

        return self._format_group(doc, group_id)

    def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Get a group by ID."""
        try:
            group = self.db.study_groups.find_one({"_id": ObjectId(group_id)})
        except Exception:
            return None
        if not group:
            return None
        formatted = self._format_group(group, str(group["_id"]))
        owner = self.db.users.find_one({"_id": ObjectId(group["owner_id"])})
        if owner:
            formatted["owner_name"] = owner["name"]
        return formatted

    def list_user_groups(self, user_id: str) -> Tuple[List[Dict[str, Any]], int]:
        """List groups the user is a member of."""
        memberships = list(self.db.study_group_members.find({"user_id": user_id}))
        group_ids = [m["group_id"] for m in memberships]
        if not group_ids:
            return [], 0

        oids = []
        for gid in group_ids:
            try:
                oids.append(ObjectId(gid))
            except Exception:
                continue

        groups = list(self.db.study_groups.find({"_id": {"$in": oids}}).sort("updated_at", -1))
        owner_ids = list(set(g["owner_id"] for g in groups))
        owner_oids = [ObjectId(oid) for oid in owner_ids]
        owners = {str(u["_id"]): u["name"] for u in self.db.users.find({"_id": {"$in": owner_oids}})}

        result = []
        for g in groups:
            f = self._format_group(g, str(g["_id"]))
            f["owner_name"] = owners.get(g["owner_id"], "Unknown")
            result.append(f)

        return result, len(result)

    def update_group(self, group_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a group. Only owner can update."""
        group = self.db.study_groups.find_one({"_id": ObjectId(group_id)})
        if not group:
            return None
        if group["owner_id"] != user_id:
            raise PermissionError("Only the group owner can update this group")

        fields = {}
        for key in ["name", "description"]:
            if key in updates and updates[key] is not None:
                fields[key] = updates[key].strip() if isinstance(updates[key], str) else updates[key]
        if not fields:
            return self._format_group(group, group_id)

        fields["updated_at"] = datetime.now(timezone.utc)
        self.db.study_groups.update_one({"_id": ObjectId(group_id)}, {"$set": fields})
        updated = self.db.study_groups.find_one({"_id": ObjectId(group_id)})
        return self._format_group(updated, group_id)

    def delete_group(self, group_id: str, user_id: str) -> bool:
        """Delete a group. Only owner can delete."""
        from app.db.cleanup import delete_group_cascade
        return delete_group_cascade(self.db, group_id, user_id)

    def generate_invite_token(self, group_id: str, user_id: str) -> str:
        """Generate invite token for a group."""
        group = self.db.study_groups.find_one({"_id": ObjectId(group_id)})
        if not group:
            raise ValueError("Group not found")
        if group["owner_id"] != user_id:
            raise PermissionError("Only the group owner can invite")

        if group.get("invite_token"):
            return group["invite_token"]

        token = secrets.token_urlsafe(32)
        self.db.study_groups.update_one(
            {"_id": ObjectId(group_id)},
            {"$set": {"invite_token": token, "updated_at": datetime.now(timezone.utc)}}
        )
        return token

    def join_by_invite(self, invite_token: str, user_id: str) -> Dict[str, Any]:
        """Join a group via invite token."""
        group = self.db.study_groups.find_one({"invite_token": invite_token})
        if not group:
            raise ValueError("Invalid or expired invite link")

        group_id = str(group["_id"])
        existing = self.db.study_group_members.find_one({"group_id": group_id, "user_id": user_id})
        if existing:
            return self._format_group(group, group_id)

        now = datetime.now(timezone.utc)
        self.db.study_group_members.insert_one({
            "group_id": group_id,
            "user_id": user_id,
            "role": "member",
            "joined_at": now,
        })

        mc = self.db.study_group_members.count_documents({"group_id": group_id})
        self.db.study_groups.update_one(
            {"_id": ObjectId(group_id)},
            {"$set": {"member_count": mc, "updated_at": now}}
        )

        updated = self.db.study_groups.find_one({"_id": ObjectId(group_id)})
        return self._format_group(updated, group_id)

    def join_group(self, group_id: str, user_id: str) -> bool:
        """Join a group directly."""
        group = self.db.study_groups.find_one({"_id": ObjectId(group_id)})
        if not group:
            return False
        existing = self.db.study_group_members.find_one({"group_id": group_id, "user_id": user_id})
        if existing:
            return True

        now = datetime.now(timezone.utc)
        self.db.study_group_members.insert_one({
            "group_id": group_id,
            "user_id": user_id,
            "role": "member",
            "joined_at": now,
        })
        mc = self.db.study_group_members.count_documents({"group_id": group_id})
        self.db.study_groups.update_one(
            {"_id": ObjectId(group_id)},
            {"$set": {"member_count": mc, "updated_at": now}}
        )
        return True

    def leave_group(self, group_id: str, user_id: str) -> bool:
        """Leave a group. Owner cannot leave."""
        group = self.db.study_groups.find_one({"_id": ObjectId(group_id)})
        if not group:
            return False
        if group["owner_id"] == user_id:
            raise PermissionError("Owner cannot leave the group")

        self.db.study_group_members.delete_one({"group_id": group_id, "user_id": user_id})
        mc = self.db.study_group_members.count_documents({"group_id": group_id})
        self.db.study_groups.update_one(
            {"_id": ObjectId(group_id)},
            {"$set": {"member_count": mc, "updated_at": datetime.now(timezone.utc)}}
        )
        return True

    def get_members(self, group_id: str) -> List[Dict[str, Any]]:
        """Get group members with names."""
        members = list(self.db.study_group_members.find({"group_id": group_id}))
        result = []
        for m in members:
            u_oid = m["user_id"] if isinstance(m["user_id"], ObjectId) else (ObjectId(m["user_id"]) if len(str(m["user_id"])) == 24 else None)
            user = self.db.users.find_one({"_id": u_oid}) if u_oid else None
            result.append({
                "user_id": str(m["user_id"]),
                "name": user["name"] if user else "Unknown",
                "role": m.get("role", "member"),
                "joined_at": m["joined_at"].isoformat() if isinstance(m.get("joined_at"), datetime) else "",
            })
        return result

    def is_member(self, group_id: str, user_id: str) -> bool:
        """Check if user is a member of the group."""
        g_refs = [group_id]
        u_refs = [user_id]
        if len(group_id) == 24:
            try:
                g_refs.append(ObjectId(group_id))
            except Exception:
                pass
        if len(user_id) == 24:
            try:
                u_refs.append(ObjectId(user_id))
            except Exception:
                pass
        return self.db.study_group_members.find_one({
            "group_id": {"$in": g_refs},
            "user_id": {"$in": u_refs}
        }) is not None

    def _format_group(self, group: Dict, group_id: str) -> Dict[str, Any]:
        return {
            "id": group_id,
            "name": group.get("name", ""),
            "description": group.get("description", ""),
            "owner_id": group.get("owner_id", ""),
            "member_count": group.get("member_count", 0),
            "invite_token": group.get("invite_token"),
            "created_at": group["created_at"].isoformat() if isinstance(group.get("created_at"), datetime) else "",
            "updated_at": group["updated_at"].isoformat() if isinstance(group.get("updated_at"), datetime) else "",
        }
