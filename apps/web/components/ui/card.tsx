import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return <section className={className ? `rounded-2xl border bg-card p-5 ${className}` : "rounded-2xl border bg-card p-5"}>{children}</section>;
}

export function CardHeader({ children }: { children: ReactNode }) {
  return <div className="flex flex-col gap-1">{children}</div>;
}

export function CardTitle({ children }: { children: ReactNode }) {
  return <h2 className="text-base font-semibold tracking-tight">{children}</h2>;
}

export function CardDescription({ children }: { children: ReactNode }) {
  return <p className="text-sm text-muted-foreground">{children}</p>;
}

export function CardContent({ children }: { children: ReactNode }) {
  return <div className="mt-4">{children}</div>;
}
