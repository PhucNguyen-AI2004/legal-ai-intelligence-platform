import { forwardRef, type ButtonHTMLAttributes } from "react";

export const Button = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" }>(
  function Button({ className = "", variant = "primary", ...props }, ref) {
    return <button ref={ref} className={`button button-${variant} ${className}`.trim()} {...props} />;
  },
);
