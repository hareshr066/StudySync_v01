import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  hoverable?: boolean;
}

export function Card({ children, hoverable = false, className = '', ...props }: CardProps) {
  return (
    <div 
      className={`
        bg-white rounded-2xl border border-surface-200 shadow-sm shadow-surface-100/50 
        ${hoverable ? 'transition-all duration-300 hover:shadow-md hover:border-primary-200 hover:-translate-y-1' : ''}
        ${className}
      `}
      {...props}
    >
      {children}
    </div>
  );
}
