import React, { useState, useEffect } from "react";
import "../styles/NameEntry.css";

interface NameEntryProps {
  onNameSubmit: (name: string) => void;
}

function NameEntry({ onNameSubmit }: NameEntryProps) {
  const [inputName, setInputName] = useState("");
  const [touched, setTouched] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const canSubmit = inputName.trim().length > 0;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (!canSubmit) return;
    setSubmitting(true);
    // slight delay for micro-animation polish
    setTimeout(() => {
      onNameSubmit(inputName.trim());
      setSubmitting(false);
    }, 220);
  };

  // allow Enter on input to trigger submit nicely on mobile
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Enter" && canSubmit) {
        e.preventDefault();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [canSubmit]);

  return (
    <div className="name-entry-page">
      {/* Ambient orbs to match hero */}
      <div className="ne-orbs">
        <div className="ne-orb ne-orb-1" />
        <div className="ne-orb ne-orb-2" />
        <div className="ne-orb ne-orb-3" />
      </div>

      <div className="ne-card fade-up" role="dialog" aria-labelledby="ne-title" aria-describedby="ne-desc">
        <h1 id="ne-title">
          Welcome<span className="ne-dot">.</span>
        </h1>
        <p id="ne-desc">Let’s get started by getting to know you</p>

        <form onSubmit={handleSubmit} className="ne-form" noValidate>
          <label className={`ne-label ${touched ? "ne-label--raised" : inputName ? "ne-label--raised" : ""}`} htmlFor="name">
            What’s your name?
          </label>
          <input
            id="name"
            type="text"
            value={inputName}
            onChange={(e) => setInputName(e.target.value)}
            onBlur={() => setTouched(true)}
            className={`ne-input ${touched && !canSubmit ? "ne-input--invalid" : ""}`}
            autoComplete="given-name"
            autoFocus
            required
            aria-invalid={touched && !canSubmit}
            aria-describedby={touched && !canSubmit ? "ne-error" : undefined}
          />
          {touched && !canSubmit && (
            <span id="ne-error" className="ne-error">
              Please enter a name.
            </span>
          )}

          <button
            type="submit"
            className={`ne-button ${submitting ? "ne-button--submitting" : ""}`}
            disabled={!canSubmit || submitting}
          >
            {submitting ? "One sec…" : "Continue"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default NameEntry;