"use client";

import { useEffect, useRef, type ReactNode } from "react";

// Mounted only while open. Native modality contains focus and makes the page inert.
export function Modal({ children, onClose, busy = false, labelledBy, describedBy, label, className = "dialog-card", alert = false }: {
  children: ReactNode;
  onClose: () => void;
  busy?: boolean;
  labelledBy?: string;
  describedBy?: string;
  label?: string;
  className?: string;
  alert?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    const trigger = document.activeElement;
    dialog?.showModal();
    return () => {
      dialog?.close();
      if (trigger instanceof HTMLElement && trigger.isConnected) trigger.focus();
    };
  }, []);

  return <dialog ref={ref} className={className} role={alert ? "alertdialog" : undefined} aria-label={label} aria-labelledby={labelledBy} aria-describedby={describedBy} aria-busy={busy} onCancel={(event) => {
    event.preventDefault();
    if (!busy) onClose();
  }}>{children}</dialog>;
}
