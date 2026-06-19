import { Link } from "react-router-dom";

export default function LandingPage() {
    return (
        <div className="container text-center mt-5">
            <h1 className="text-success">🌿 Irrigo</h1>
            <p className="text-muted">
                Smart irrigation system management platform
            </p>

            <Link className="btn btn-success mt-3" to="/login">
                Login
            </Link>
        </div>
    );
}