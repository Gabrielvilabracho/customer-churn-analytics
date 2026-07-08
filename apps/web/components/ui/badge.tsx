import type { ReactNode } from "react";

const BADGE_VARIANTS = {
  default: "border-transparent bg-primary text-primary-foreground",
  secondary: "border-transparent bg-secondary text-secondary-foreground",
  outline: "text-foreground",
} as const;

type BadgeVariant = keyof typeof BADGE_VARIANTS;

interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
}

export function Badge({ children, variant = "secondary" }: BadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${BADGE_VARIANTS[variant]}`}>
      {children}
    </span>
  );
}
