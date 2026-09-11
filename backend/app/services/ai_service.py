import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        else:
            self.client = None
            logger.warning("GEMINI_API_KEY is not set. AI capabilities will be disabled.")
        
        self.model_name = settings.GEMINI_MODEL

    def is_available(self) -> bool:
        return self.client is not None

    def _get_context_files(self, context_type: Optional[str], context_id: Optional[str], owner_id: str) -> List[Dict[str, Any]]:
        if not context_type or not context_id:
            return []
            
        from app.db.mongodb import get_database
        from bson import ObjectId
        import os, pathlib
        db = get_database()
        files = []

        u_refs = [owner_id]
        if len(str(owner_id)) == 24:
            try:
                u_refs.append(ObjectId(str(owner_id)))
            except Exception:
                pass

        upload_dir = (pathlib.Path(__file__).parent.parent.parent / "data" / "uploads").resolve()

        def make_entry(doc):
            doc_id_str = str(doc["_id"])
            ext = os.path.splitext(doc.get("filename", ""))[1]
            local_path = (upload_dir / f"{doc_id_str}{ext}").resolve()
            if not local_path.exists():
                matches = list(upload_dir.glob(f"{doc_id_str}*"))
                if matches:
                    local_path = matches[0]
            
            return {
                "id": doc.get("gemini_file_id"),
                "name": doc.get("filename", doc.get("title", "document")),
                "doc_id": doc_id_str,
                "local_path": str(local_path) if local_path.exists() else None,
                "mime_type": doc.get("mime_type", "")
            }

        if context_type == "document":
            c_refs = [context_id]
            if len(str(context_id)) == 24:
                try:
                    c_refs.append(ObjectId(str(context_id)))
                except Exception:
                    pass
            doc = db.documents.find_one({"_id": {"$in": c_refs}, "owner_id": {"$in": u_refs}})
            if doc:
                files.append(make_entry(doc))
        elif context_type == "notebook":
            nb_refs = [context_id]
            if len(str(context_id)) == 24:
                try:
                    nb_refs.append(ObjectId(str(context_id)))
                except Exception:
                    pass
            nb = db.notebooks.find_one({"_id": {"$in": nb_refs}, "owner_id": {"$in": u_refs}})
            if nb and "documents" in nb:
                doc_keys = nb["documents"]
                doc_query_keys = []
                for k in doc_keys:
                    doc_query_keys.append(k)
                    if isinstance(k, str) and len(k) == 24:
                        try:
                            doc_query_keys.append(ObjectId(k))
                        except Exception:
                            pass
                    elif isinstance(k, ObjectId):
                        doc_query_keys.append(str(k))
                docs = db.documents.find({"_id": {"$in": doc_query_keys}, "owner_id": {"$in": u_refs}})
                for doc in docs:
                    files.append(make_entry(doc))
        return files

    def _resolve_context_contents(self, context_files: List[Dict[str, Any]]) -> tuple[List[Any], List[Dict[str, Any]]]:
        """Resolve Gemini File objects or local file text for model input."""
        contents = []
        citations_metadata = []
        for f in context_files:
            resolved = False
            # 1. Try existing gemini_file_id
            if f.get("id"):
                try:
                    g_file = self.client.files.get(name=f["id"])
                    contents.append(g_file)
                    citations_metadata.append(f)
                    resolved = True
                except Exception as e:
                    logger.warning(f"Could not retrieve gemini file {f['id']}: {e}")

            # 2. Try on-the-fly upload of local file if not resolved
            if not resolved and f.get("local_path"):
                try:
                    g_file = self.client.files.upload(
                        file=f["local_path"],
                        config={'display_name': f["name"]}
                    )
                    contents.append(g_file)
                    citations_metadata.append(f)
                    resolved = True
                except Exception as e:
                    logger.warning(f"On-the-fly Gemini upload failed for {f['name']}: {e}")

            # 3. Text fallback for readable files
            if not resolved and f.get("local_path"):
                try:
                    with open(f["local_path"], "r", encoding="utf-8", errors="ignore") as tf:
                        text_snippet = tf.read(20000)
                        if text_snippet.strip():
                            contents.append(f"=== SOURCE DOCUMENT: {f['name']} ===\n{text_snippet}\n=== END SOURCE ===")
                            citations_metadata.append(f)
                            resolved = True
                except Exception:
                    pass

        return contents, citations_metadata

    async def generate_response(
        self, prompt: str, context_type: Optional[str], context_id: Optional[str], owner_id: str, mode: str
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise Exception("AI service is unavailable.")

        import re
        system_instruction = "You are StudySync's source-grounded learning assistant.\n"
        system_instruction += "For questions about the user's notebook sources:\n"
        system_instruction += "- prioritize retrieved source content\n"
        system_instruction += "- distinguish retrieved information from general knowledge\n"
        system_instruction += "- if the answer cannot be established from the sources, explicitly say so\n"
        system_instruction += "- cite retrieved sources when available using inline citations like [filename, p. X] or [filename].\n\n"
        
        if mode == "explain":
            system_instruction += "Explain clearly, use step-by-step reasoning, and remain grounded in sources."
        elif mode == "socratic":
            system_instruction += "Guide the student with probing questions, don't immediately reveal answers, and foster critical thinking."
        elif mode == "deep_dive":
            system_instruction += "Provide technical depth, compare concepts, analyze implications, and cite specific passages."
        elif mode == "summarize":
            system_instruction += "Provide a comprehensive, highly structured executive summary of the provided sources."

        contents = []
        citations_metadata = []
        if context_type and context_id:
            context_files = self._get_context_files(context_type, context_id, owner_id)
            c_contents, c_metadata = self._resolve_context_contents(context_files)
            contents.extend(c_contents)
            citations_metadata.extend(c_metadata)
            
            if not contents:
                prompt_text = f"User Question: {prompt}\n\n(Note: No uploaded source documents are currently attached or ready.)"
            else:
                prompt_text = f"User Question: {prompt}\n\nPlease answer grounded primarily in the attached study material. If citing, note the document name and page number if known."
        else:
            prompt_text = prompt

        contents.append(prompt_text)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3
                )
            )
            
            text = response.text or ""
            final_citations = []
            
            # Grounding and citation extraction
            for meta in citations_metadata:
                fname = meta["name"]
                # Look for filename or citations in generated text
                if fname.lower() in text.lower():
                    # Attempt to extract page number if referenced: e.g., "p. 12" or "page 12"
                    page_num = None
                    page_match = re.search(rf"(?:{re.escape(fname)}).*?(?:page|p\.?)\s*(\d+)", text, re.IGNORECASE)
                    if page_match:
                        try:
                            page_num = int(page_match.group(1))
                        except Exception:
                            page_num = None

                    final_citations.append({
                        "doc_id": meta.get("doc_id", ""),
                        "source_id": meta.get("id") or meta.get("doc_id", ""),
                        "source_name": fname,
                        "page_number": page_num
                    })
            
            return {
                "text": text,
                "citations": final_citations
            }
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")

    async def generate_quiz(
        self, context_type: Optional[str], context_id: Optional[str], owner_id: str,
        count: int = 5, difficulty: str = "medium", quiz_type: str = "mcq"
    ) -> List[Dict[str, Any]]:
        if not self.is_available():
            raise Exception("AI service is unavailable.")
            
        class QuizQuestion(BaseModel):
            question: str
            options: List[str]
            correct_answer: str
            explanation: str
            difficulty: str
            
        contents = []
        if context_type and context_id:
            context_files = self._get_context_files(context_type, context_id, owner_id)
            c_contents, _ = self._resolve_context_contents(context_files)
            contents.extend(c_contents)
                    
        prompt_text = f"Generate {count} {quiz_type} questions of {difficulty} difficulty based on the provided documents. Focus on key concepts. For MCQ provide 4 options. For true/false provide 2 options: ['True', 'False']."
        contents.append(prompt_text)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=list[QuizQuestion],
                    temperature=0.2
                )
            )
            import json
            raw = response.text or "[]"
            cleaned = raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception as e:
            logger.error(f"Gemini API error generating quiz: {e}")
            raise Exception("Failed to generate quiz.")

    async def generate_study_plan(
        self, goal: str, exam_date: str, minutes_per_day: int,
        deck_ids: List[str], owner_id: str
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise Exception("AI service is unavailable.")
            
        class DayPlan(BaseModel):
            day: int
            date: str
            topic: str
            activity: str
            duration_minutes: int
            tips: str

        try:
            # Let's count days roughly or just ask the model to generate based on exam_date
            prompt = f"Create a detailed study plan for: Goal: {goal}. Exam date: {exam_date}. Available time: {minutes_per_day} minutes/day. Output a structured day-by-day plan."
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=list[DayPlan],
                    temperature=0.2
                )
            )
            import json
            days = json.loads(response.text)
            return {"goal": goal, "exam_date": exam_date, "days": days}
        except Exception as e:
            logger.error(f"Gemini API error generating study plan: {e}")
            raise Exception("Failed to generate study plan.")

    async def generate_flashcards(
        self, count: int, difficulty: str, context_type: Optional[str] = None, context_id: Optional[str] = None,
        owner_id: str = "", text: str = ""
    ) -> List[Dict[str, Any]]:
        if not self.is_available():
            raise Exception("AI service is unavailable.")
        
        class Flashcard(BaseModel):
            front: str
            back: str
            tags: List[str]
            difficulty: str

        contents = []
        if context_type and context_id:
            context_files = self._get_context_files(context_type, context_id, owner_id)
            c_contents, _ = self._resolve_context_contents(context_files)
            contents.extend(c_contents)
        elif text:
            contents.append(text)
            
        prompt = f"Generate {count} flashcards of {difficulty} difficulty from the provided content. Ensure clear question/prompt on front and concise factual answer on back."
        contents.append(prompt)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=list[Flashcard],
                    temperature=0.2
                )
            )
            import json
            raw = response.text or "[]"
            cleaned = raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception as e:
            logger.error(f"Gemini API error generating flashcards: {e}")
            raise Exception("Failed to generate flashcards.")

    async def upload_document_to_gemini(self, file_path: str, mime_type: str, display_name: str) -> str:
        """Upload a file to Gemini and return the Gemini File ID."""
        if not self.is_available():
            return ""
        try:
            uploaded_file = self.client.files.upload(
                file=file_path,
                config={'display_name': display_name}
            )
            return uploaded_file.name
        except Exception as e:
            logger.error(f"Failed to upload to Gemini: {e}")
            raise e

    async def delete_document_from_gemini(self, gemini_file_id: str):
        """Delete a file from Gemini."""
        if not self.is_available():
            return
        try:
            self.client.files.delete(name=gemini_file_id)
        except Exception as e:
            logger.error(f"Failed to delete from Gemini: {e}")

ai_service = AIService()
