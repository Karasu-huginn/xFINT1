import { useState } from "react";
import type { FormEvent } from "react";
import { Navigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../auth/useAuth";
import Alert from "../components/Alert";
import Button from "../components/Button";
import Field, { INPUT_CLASSES } from "../components/Field";
import Sheet from "../components/Sheet";

export default function LoginPage() {
  const { currentUser, signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [failureMessage, setFailureMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFailureMessage(null);
    setIsSubmitting(true);
    try {
      await signIn(email, password);
    } catch (error) {
      setFailureMessage(
        // Login is the one place a 401 has a precise meaning, so the page
        // supplies it rather than letting the generic session message through.
        error instanceof ApiError && error.status === 401
          ? "Adresse e-mail ou mot de passe incorrect."
          : "Connexion impossible, merci de réessayer.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  if (currentUser !== null) {
    return <Navigate to="/" replace />;
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-canvas p-4">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-semibold text-primary">SUP Herman</h1>
          <p className="text-sm text-muted">Gestion des notes de frais</p>
        </div>
        <Sheet title="Connexion">
          {failureMessage !== null && <Alert tone="error">{failureMessage}</Alert>}
          <form onSubmit={handleSubmit} noValidate>
            <Field label="Adresse e-mail" htmlFor="email">
              <input
                id="email"
                type="email"
                autoComplete="username"
                required
                className={INPUT_CLASSES}
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </Field>
            <Field label="Mot de passe" htmlFor="password">
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                className={INPUT_CLASSES}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </Field>
            <Button
              type="submit"
              variant="primary"
              className="w-full"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Connexion..." : "Se connecter"}
            </Button>
          </form>
        </Sheet>
      </div>
    </main>
  );
}
