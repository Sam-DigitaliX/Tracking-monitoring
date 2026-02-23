import { forwardRef, type SelectHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        "flex h-10 w-full rounded-lg border border-glass-border bg-card backdrop-blur-md px-3 py-2 text-sm transition-all",
        "focus:outline-none focus:border-primary/50 focus:shadow-[0_0_0_3px_hsl(262_83%_58%/0.08),0_0_20px_hsl(262_83%_58%/0.04)]",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    >
      {children}
    </select>
  )
);
Select.displayName = "Select";

export { Select };
