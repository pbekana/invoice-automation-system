/**
 * Class name utility for merging Tailwind classes
 * Uses clsx for conditional classes and tailwind-merge to resolve conflicts
 */
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
