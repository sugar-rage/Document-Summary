import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { session, sendOtp, verifyOtp } = useAuth();
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState<"email" | "otp">("email");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  if (session) {
    return <Navigate to="/" replace />;
  }

  async function onSend(event: FormEvent) {
    event.preventDefault();
    setError("");
    setInfo("");
    setBusy(true);
    try {
      await sendOtp(email.trim());
      setStep("otp");
      setInfo("Check your email for a one-time code. It may take a minute, and it can land in spam.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send OTP.");
    } finally {
      setBusy(false);
    }
  }

  async function onVerify(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await verifyOtp(email.trim(), otp.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid or expired OTP.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="center-page">
      <section className="card auth-card">
        <h1>Document Summary Assistant</h1>
        <p className="muted">Sign in with an email one-time code. No password is stored.</p>

        {step === "email" ? (
          <form onSubmit={onSend} className="stack">
            <label>
              Email
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </label>
            <button type="submit" disabled={busy}>
              {busy ? "Sending OTP..." : "Send OTP"}
            </button>
          </form>
        ) : (
          <form onSubmit={onVerify} className="stack">
            <label>
              One-time code
              <input
                inputMode="numeric"
                required
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                autoComplete="one-time-code"
              />
            </label>
            <button type="submit" disabled={busy}>
              {busy ? "Verifying..." : "Verify OTP"}
            </button>
            <button
              type="button"
              className="secondary"
              disabled={busy}
              onClick={() => void onSend({ preventDefault() {} } as FormEvent)}
            >
              Resend OTP
            </button>
            <button type="button" className="linkish" onClick={() => setStep("email")}>
              Use a different email
            </button>
          </form>
        )}
        {info ? <p className="success">{info}</p> : null}
        {error ? <p className="error">{error}</p> : null}
      </section>
    </div>
  );
}
