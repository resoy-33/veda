import { Link } from "react-router-dom";

export function Brand({ to, compact = false }) {
  const content = (
    <>
      <span className="brand-mark" aria-hidden="true">
        V
      </span>
      <span className="brand-copy">
        <span className="brand-word">Veda</span>
        {!compact && (
          <span className="brand-tagline">Dépôts financiers vérifiés</span>
        )}
      </span>
    </>
  );

  if (to) {
    return (
      <Link to={to} className="brand" aria-label="Veda — accueil">
        {content}
      </Link>
    );
  }
  return <div className="brand">{content}</div>;
}
