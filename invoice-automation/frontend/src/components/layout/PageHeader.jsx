import { cn } from '../../utils/cn';

export function PageHeader({ 
  title, 
  description, 
  action, 
  breadcrumbs,
  className 
}) {
  return (
    <div className={cn('mb-6', className)}>
      {breadcrumbs && (
        <nav className="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400 mb-2">
          {breadcrumbs.map((crumb, idx) => (
            <div key={idx} className="flex items-center gap-2">
              {idx > 0 && <span className="text-neutral-400 dark:text-neutral-600">/</span>}
              {crumb.href ? (
                <a href={crumb.href} className="hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors">
                  {crumb.label}
                </a>
              ) : (
                <span className="text-neutral-900 dark:text-neutral-100 font-medium">{crumb.label}</span>
              )}
            </div>
          ))}
        </nav>
      )}
      
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">{title}</h1>
          {description && (
            <p className="text-neutral-600 dark:text-neutral-400 mt-1">{description}</p>
          )}
        </div>
        {action && <div className="flex-shrink-0">{action}</div>}
      </div>
    </div>
  );
}
