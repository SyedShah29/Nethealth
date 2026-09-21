"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function DiagnosticsSearchPage() {
  const [subscriberId, setSubscriberId] = useState("");
  const router = useRouter();
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (subscriberId.trim()) router.push(`/diagnostics/${encodeURIComponent(subscriberId.trim())}`);
  };
  return <main className="foundation operations"><p className="eyebrow">Phase 12 · Customer 360</p><h1>Subscriber diagnostics</h1><form className="diagnostic-search" onSubmit={submit}><label htmlFor="subscriber-id">Subscriber ID</label><input id="subscriber-id" value={subscriberId} onChange={(event) => setSubscriberId(event.target.value)} /><button type="submit">Investigate</button></form></main>;
}
