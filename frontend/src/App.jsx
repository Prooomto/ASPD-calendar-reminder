import { Routes, Route, Link, Navigate, useLocation } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Events from "./pages/Events";
import Companies from "./pages/Companies";
import CompanyDetails from "./pages/CompanyDetails";


function Private({ children }) {
  const token = localStorage.getItem("token");
  return token ? children : <Navigate to="/register" replace />;
}

// если есть токен — на события, иначе — на регистрацию
function HomeRedirect() {
  const token = localStorage.getItem("token");
  return <Navigate to={token ? "/events" : "/register"} replace />;
}

function Nav() {
  const loc = useLocation();
  const token = localStorage.getItem("token");

  function logout() {
    localStorage.removeItem("token");
    window.location.href = "/register";
  }

  const linkStyle = (path) => ({
    textDecoration: "none",
    fontWeight: loc.pathname === path ? "700" : "500",
    color: loc.pathname === path ? "#5b52ff" : "#333",
    padding: "6px 10px",
    borderRadius: "8px",
    transition: "0.2s ease",
    background: loc.pathname === path ? "rgba(91,82,255,0.1)" : "transparent",
  });

  return (
    <nav
      style={{
        padding: "10px 16px",
        borderBottom: "1px solid #eee",
        display: "flex",
        alignItems: "center",
        gap: 12,
        position: "sticky",
        top: 0,
        zIndex: 50,
        background: "rgba(255,255,255,0.8)",
        backdropFilter: "blur(8px)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <Link to="/events" style={linkStyle("/events")}>
          События
        </Link>
          <Link to="/companies" style={linkStyle("/companies")}>Компании</Link>

        <Link to="/register" style={linkStyle("/register")}>
          Регистрация
        </Link>
        <Link to="/login" style={linkStyle("/login")}>
          Вход
        </Link>

      </div>

      <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 10 }}>
        {token && loc.pathname !== "/events" && (
          <Link to="/events" style={linkStyle("/events")}>
            К событиям
          </Link>
        )}
        {token && (
          <button
            onClick={logout}
            style={{
              border: 0,
              padding: "6px 14px",
              borderRadius: "8px",
              fontWeight: "600",
              background: "#f3f3f5",
              cursor: "pointer",
              color: "#333",
              transition: "0.2s",
            }}
            onMouseOver={(e) => (e.target.style.background = "#ececf1")}
            onMouseOut={(e) => (e.target.style.background = "#f3f3f5")}
          >
            Выйти
          </button>
        )}
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <>
      <Nav />
      <Routes>
        <Route path="/" element={<HomeRedirect />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/events"
          element={
            <Private>
              <Events />
            </Private>
          }
        />
        <Route
  path="/companies"
  element={
    <Private>
      <Companies />
    </Private>
  }
/>
<Route
  path="/companies/:id"
  element={
    <Private>
      <CompanyDetails />
    </Private>
  }
/>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
