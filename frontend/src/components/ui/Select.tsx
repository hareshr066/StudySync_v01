import type { SelectHTMLAttributes } from 'react';

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  className?: string;
}

export function Select({ className = '', children, ...props }: SelectProps) {
  return (
    <select
      className={`block w-full rounded-md border-surface-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm ${className}`}
      {...props}
    >
      {children}
    </select>
  );
}
