import type { ButtonHTMLAttributes } from "react";

export function IconButton({ label, className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return <button type="button" className={`icon-button ${className}`.trim()} aria-label={label} title={label} {...props} />;
}
