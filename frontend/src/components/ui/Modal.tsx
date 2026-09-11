import React, { useEffect } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
}

export function Modal({ isOpen, onClose, title, children, maxWidth = 'md' }: ModalProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const maxWidthClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    full: 'max-w-[95vw]',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-surface-900/40 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      
      {/* Dialog */}
      <div 
        className={`relative w-full ${maxWidthClasses[maxWidth]} bg-white rounded-2xl shadow-xl shadow-surface-900/10 border border-surface-100 flex flex-col max-h-[90vh] overflow-hidden animate-in fade-in zoom-in-95 duration-200`}
        onClick={e => e.stopPropagation()}
      >
        {title && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-surface-100">
            <h2 className="text-lg font-semibold text-surface-900">{title}</h2>
            <button 
              onClick={onClose}
              className="text-surface-400 hover:text-surface-600 transition-colors p-1 rounded-lg hover:bg-surface-50"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        )}
        {!title && (
          <button 
            onClick={onClose}
            className="absolute top-4 right-4 text-surface-400 hover:text-surface-600 transition-colors p-1 rounded-lg hover:bg-surface-50 z-10"
          >
            <X className="w-5 h-5" />
          </button>
        )}
        
        <div className="p-6 overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
}
