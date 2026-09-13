import { Scale } from "lucide-react";

export function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <div className="brand" aria-label="Legal AI">
      <span className="brand-mark"><Scale size={19} aria-hidden="true" /></span>
      {!compact && <span>Legal AI</span>}
    </div>
  );
}
