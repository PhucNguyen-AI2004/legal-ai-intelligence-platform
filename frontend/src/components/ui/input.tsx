import type { InputHTMLAttributes, ReactNode } from "react";

export function Input({ label, hideLabel = false, icon, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string; hideLabel?: boolean; icon?: ReactNode }) {
  const id = props.id ?? props.name ?? label.toLowerCase().replaceAll(" ", "-");
  return <label className="field" htmlFor={id}><span className={hideLabel ? "sr-only" : "field-label"}>{label}</span><span className="input-wrap">{icon}<input id={id} {...props} /></span></label>;
}
