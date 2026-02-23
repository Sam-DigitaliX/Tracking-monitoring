import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      ref={ref}
      className={cn(
        "flex h-10 w-full rounded-lg border border-glass-border bg-card backdrop-blur-md px-3 py-2 text-sm transition-all",
        "placeholder:text-muted-foreground",
        "focus:outline-none focus:border-primary/50 focus:shadow-[0_0_0_3px_hsl(262_83%_58%/0.08),0_0_20px_hsl(262_83%_58%/0.04)]",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";

export { Input };
