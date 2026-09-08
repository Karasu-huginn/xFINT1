import { useState } from "react";
import type { FormEvent } from "react";

import { ApiError } from "../api/client";
import { buildActivationUrl, createUser } from "../api/users";
import Alert from "../components/Alert";
import Button from "../components/Button";
import ControlPanel from "../components/ControlPanel";
import Field, { INPUT_CLASSES } from "../components/Field";
import Sheet from "../components/Sheet";
import { ROLE_LABELS, describeApiError } from "../labels/fr";
import type { Role } from "../types/api";

const ASSIGNABLE_ROLES: Role[] = ["EMPLOYEE", "MANAGER", "ACCOUNTING"];

export default function NewUserPage() {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Role>("EMPLOYEE");
  const [activationUrl, setActivationUrl] = useState<string | null>(null);
  const [failureMessage, setFailureMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFailureMessage(null);
    setActivationUrl(null);
    try {
      const invited = await createUser(email, role);
      setActivationUrl(buildActivationUrl(invited.activation_token));
      setEmail("");
    } catch (error) {
      setFailureMessage(
        error instanceof ApiError
          ? describeApiError(error.code, "La création du compte a échoué.")
          : "La création du compte a échoué.",
      );
    }
  }

  return (
    <>
      <ControlPanel title="Créer un compte" />
      <main className="mx-auto max-w-6xl p-4">
        <Sheet>
          {failureMessage !== null && <Alert tone="error">{failureMessage}</Alert>}
          {activationUrl !== null && (
            <Alert tone="success">
              <p className="mb-2 font-medium">
                Compte créé. Transmettez ce lien d&apos;activation à son titulaire.
              </p>
              <code className="block break-all rounded bg-white px-2 py-1 text-xs text-ink">
                {activationUrl}
              </code>
              <p className="mt-2 text-xs">
                Ce lien n&apos;est affiché qu&apos;une seule fois et expire dans 7 jours.
              </p>
            </Alert>
          )}
          <form onSubmit={handleSubmit} noValidate>
            <Field label="Adresse e-mail" htmlFor="email">
              <input
                id="email"
                type="email"
                required
                className={INPUT_CLASSES}
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </Field>
            <Field label="Rôle" htmlFor="role">
              <select
                id="role"
                className={INPUT_CLASSES}
                value={role}
                onChange={(event) => setRole(event.target.value as Role)}
              >
                {ASSIGNABLE_ROLES.map((assignableRole) => (
                  <option key={assignableRole} value={assignableRole}>
                    {ROLE_LABELS[assignableRole]}
                  </option>
                ))}
              </select>
            </Field>
            <Button type="submit" variant="primary">
              Créer le compte
            </Button>
          </form>
        </Sheet>
      </main>
    </>
  );
}
