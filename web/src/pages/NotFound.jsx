import { Link } from "react-router-dom";
import { ArrowLeft, Compass } from "lucide-react";
import { useAuth } from "../auth/AuthContext.jsx";
import { Brand } from "../components/Brand.jsx";

export function NotFound() {
  const { isAuthenticated } = useAuth();
  const target = isAuthenticated ? "/depots" : "/login";

  return (
    <main className="notfound">
      <Brand />
      <span className="notfound-code">404</span>
      <h1>Cette page n’existe pas.</h1>
      <p>Le registre reste intact — revenez à l’essentiel.</p>
      <Link to={target} className="btn btn-primary">
        <ArrowLeft size={17} />
        {isAuthenticated ? "Retour aux dépôts" : "Retour à la connexion"}
      </Link>
      <Compass size={40} className="notfound-icon" />
    </main>
  );
}
