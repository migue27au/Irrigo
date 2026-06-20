import { Link } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function AppNavbar() {
    const { token, logout, user } = useAuth();

    const isDisabled = !token;

    const navigate = useNavigate();
    const handleLogout = () => {
        logout();
        navigate("/");
    };
    
    const DisabledItem = ({ children }) => (
        <span className="nav-link disabled-link">
            {children}
        </span>
    );

    return (
    <nav className="navbar navbar-expand-lg navbar-dark px-3 irrigo-navbar">
        <div className="container-fluid">

        <Link className="navbar-brand fw-bold text-success" to="/">🌿 Irrigo</Link>

        <div className="vr mx-3 text-secondary"></div>

        <div className="navbar-nav me-auto">
            {isDisabled ? (
                <DisabledItem>Systems</DisabledItem>
            ) : (
                <Link className="nav-link" to="/systems">Systems</Link>
            )}

            {isDisabled ? (
                <DisabledItem>Measures</DisabledItem>
            ) : (
                <Link className="nav-link" to="/measures">Measures</Link>
            )}

        </div>

        <div className="d-flex align-items-center gap-3">
            <div className="vr mx-3 text-secondary"></div>
            {isDisabled ? (
                <DisabledItem>Profile</DisabledItem>
            ) : (
                <span className="nav-link text-success fw-semibold">
                    {user?.username || "user"}
                </span>
            )}
            <button className="btn btn-outline-success btn-sm" onClick={handleLogout} disabled={isDisabled}>Logout</button>
        </div>

        </div>
    </nav>
    );
}