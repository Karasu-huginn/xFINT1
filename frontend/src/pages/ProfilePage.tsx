import { useAuth } from "../auth/useAuth";
import ControlPanel from "../components/ControlPanel";
import Sheet from "../components/Sheet";
import { ROLE_LABELS } from "../labels/fr";

export default function ProfilePage() {
  const { currentUser } = useAuth();

  if (currentUser === null) {
    return null;
  }

  return (
    <>
      <ControlPanel title="Mon profil" />
      <main className="mx-auto max-w-6xl p-4">
        <Sheet>
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-xs uppercase tracking-wide text-muted">
                Adresse e-mail
              </dt>
              <dd className="text-ink">{currentUser.email}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-muted">Rôle</dt>
              <dd className="text-ink">{ROLE_LABELS[currentUser.role]}</dd>
            </div>
          </dl>
        </Sheet>
      </main>
    </>
  );
}
