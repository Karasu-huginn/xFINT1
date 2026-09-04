import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { activateAccount, probeActivation } from "../api/auth";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/useAuth";
import Alert from "../components/Alert";
import Button from "../components/Button";
import Field, { INPUT_CLASSES } from "../components/Field";
import Sheet from "../components/Sheet";
import { describeApiError } from "../labels/fr";

const WEAK_PASSWORD_MESSAGE =
  "Ce mot de passe est trop faible. Il faut au moins 8 caractères, dont une lettre et un chiffre.";

const INVALID_LINK_MESSAGE =
  "Ce lien d'activation est invalide ou a expiré. Demandez-en un nouveau à votre manager.";

export default function ActivatePage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const token = searchParams.get("token") ?? "";
  const [invitedEmail, setInvitedEmail] = useState<string | null>(null);
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [failureMessage, setFailureMessage] = useState<string | null>(null);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    probeActivation(token)
      .then((probe) => setInvitedEmail(probe.email))
      .catch(() => setFailureMessage(INVALID_LINK_MESSAGE))
      .finally(() => setIsChecking(false));
  }, [token]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFailureMessage(null);
    if (password !== confirmation) {
      setFailureMessage("Les deux mots de passe ne correspondent pas.");
      return;
    }
    try {
      await activateAccount(token, password);
      await refresh();
      navigate("/", { replace: true });
    } catch (error) {
      setFailureMessage(
        error instanceof ApiError
          ? describeApiError(error.code, WEAK_PASSWORD_MESSAGE)
          : INVALID_LINK_MESSAGE,
      );
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-canvas p-4">
      <div className="w-full max-w-md">
        <h1 className="mb-6 text-center text-2xl font-semibold text-primary">
          SUP Herman
        </h1>
        <Sheet title="Première connexion">
          {isChecking && <p className="text-muted">Vérification du lien...</p>}
          {failureMessage !== null && <Alert tone="error">{failureMessage}</Alert>}
          {invitedEmail !== null && (
            <form onSubmit={handleSubmit} noValidate>
              <p className="mb-4 text-sm text-muted">
                Compte : <span className="font-medium text-ink">{invitedEmail}</span>
              </p>
              <Field
                label="Choisissez un mot de passe"
                htmlFor="password"
                hint="8 caractères minimum, dont au moins une lettre et un chiffre."
              >
                <input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  className={INPUT_CLASSES}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
              </Field>
              <Field label="Confirmez le mot de passe" htmlFor="confirmation">
                <input
                  id="confirmation"
                  type="password"
                  autoComplete="new-password"
                  required
                  className={INPUT_CLASSES}
                  value={confirmation}
                  onChange={(event) => setConfirmation(event.target.value)}
                />
              </Field>
              <Button type="submit" variant="primary" className="w-full">
                Activer mon compte
              </Button>
            </form>
          )}
        </Sheet>
      </div>
    </main>
  );
}
