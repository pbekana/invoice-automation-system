import { forwardRef } from 'react';
import { cn } from '../../utils/cn';

export const Input = forwardRef(({ 
  label,
  error,
  hint,
  icon: Icon,
  className,
  containerClassName,
  ...props 
}, ref) => {
  return (
    <div className={cn('space-y-1.5', containerClassName)}>
      {label && (
        <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
          {label}
          {props.required && <span className="text-error-500 ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
            <Icon className="w-4 h-4 text-neutral-400 dark:text-neutral-500" />
          </div>
        )}
        <input
          ref={ref}
          className={cn(
            'w-full px-3 py-2 rounded-lg border bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100',
            'placeholder:text-neutral-400 dark:placeholder:text-neutral-500',
            'transition-colors duration-200',
            'focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent',
            'disabled:bg-neutral-50 dark:disabled:bg-neutral-900 disabled:cursor-not-allowed disabled:text-neutral-500 dark:disabled:text-neutral-600',
            error ? 'border-error-500 focus:ring-error-500' : 'border-neutral-300 dark:border-neutral-700',
            Icon && 'pl-10',
            className
          )}
          {...props}
        />
      </div>
      {hint && !error && (
        <p className="text-xs text-neutral-500 dark:text-neutral-400">{hint}</p>
      )}
      {error && (
        <p className="text-xs text-error-600 dark:text-error-400 flex items-center gap-1">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          {error}
        </p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export const Textarea = forwardRef(({ 
  label,
  error,
  hint,
  className,
  containerClassName,
  rows = 4,
  ...props 
}, ref) => {
  return (
    <div className={cn('space-y-1.5', containerClassName)}>
      {label && (
        <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
          {label}
          {props.required && <span className="text-error-500 ml-1">*</span>}
        </label>
      )}
      <textarea
        ref={ref}
        rows={rows}
        className={cn(
          'w-full px-3 py-2 rounded-lg border bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100',
          'placeholder:text-neutral-400 dark:placeholder:text-neutral-500',
          'transition-colors duration-200',
          'focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent',
          'disabled:bg-neutral-50 dark:disabled:bg-neutral-900 disabled:cursor-not-allowed disabled:text-neutral-500 dark:disabled:text-neutral-600',
          'resize-none',
          error ? 'border-error-500 focus:ring-error-500' : 'border-neutral-300 dark:border-neutral-700',
          className
        )}
        {...props}
      />
      {hint && !error && (
        <p className="text-xs text-neutral-500 dark:text-neutral-400">{hint}</p>
      )}
      {error && (
        <p className="text-xs text-error-600 dark:text-error-400">{error}</p>
      )}
    </div>
  );
});

Textarea.displayName = 'Textarea';
