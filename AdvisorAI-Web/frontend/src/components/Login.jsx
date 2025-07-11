import React, { useState } from "react";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please enter both email and password.");
      return;
    }
    setError("");
    alert("Logged in!");
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100vw",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Decorative circles */}
      <div
        style={{
          position: "absolute",
          top: "-120px",
          left: "-120px",
          width: "300px",
          height: "300px",
          borderRadius: "50%",
          background: "rgba(167,119,227,0.15)",
          zIndex: 0,
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: "-100px",
          right: "-100px",
          width: "220px",
          height: "220px",
          borderRadius: "50%",
          background: "rgba(110,142,251,0.12)",
          zIndex: 0,
        }}
      />

      <form
        onSubmit={handleSubmit}
        style={{
          position: "relative",
          zIndex: 1,
          background: "rgba(255,255,255,0.92)",
          padding: "3.5rem 2.5rem",
          borderRadius: "2rem",
          boxShadow: "0 16px 48px 0 rgba(31, 38, 135, 0.22)",
          display: "flex",
          flexDirection: "column",
          width: "100%",
          maxWidth: "420px",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <img
            src="https://cdn-icons-png.flaticon.com/512/295/295128.png"
            alt="Logo"
            style={{ width: 64, marginBottom: 12 }}
          />
          <h1
            style={{
              color: "#6e8efb",
              margin: 0,
              fontWeight: 800,
              fontSize: "2.2rem",
            }}
          >
            Welcome Back
          </h1>
          <p style={{ color: "#888", marginTop: 8, fontSize: "1.1rem" }}>
            Sign in to your AdvisorAI account
          </p>
        </div>
        <label
          style={{
            marginBottom: "0.5rem",
            fontWeight: "bold",
            color: "#6e8efb",
          }}
        >
          Email Address
        </label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{
            padding: "1rem",
            marginBottom: "1.2rem",
            borderRadius: "0.75rem",
            border: "1.5px solid #e0e0e0",
            fontSize: "1.05rem",
            outline: "none",
            background: "#f7f8fa",
            transition: "border 0.2s",
          }}
          placeholder="you@example.com"
          onFocus={(e) => (e.target.style.border = "1.5px solid #6e8efb")}
          onBlur={(e) => (e.target.style.border = "1.5px solid #e0e0e0")}
        />
        <label
          style={{
            marginBottom: "0.5rem",
            fontWeight: "bold",
            color: "#6e8efb",
          }}
        >
          Password
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{
            padding: "1rem",
            marginBottom: "1.2rem",
            borderRadius: "0.75rem",
            border: "1.5px solid #e0e0e0",
            fontSize: "1.05rem",
            outline: "none",
            background: "#f7f8fa",
            transition: "border 0.2s",
          }}
          placeholder="Enter your password"
          onFocus={(e) => (e.target.style.border = "1.5px solid #6e8efb")}
          onBlur={(e) => (e.target.style.border = "1.5px solid #e0e0e0")}
        />
        {error && (
          <div
            style={{
              color: "#e74c3c",
              marginBottom: "1rem",
              textAlign: "center",
              fontWeight: "bold",
            }}
          >
            {error}
          </div>
        )}
        <button
          type="submit"
          style={{
            background: "linear-gradient(90deg, #6e8efb 0%, #a777e3 100%)",
            color: "#fff",
            padding: "1rem",
            border: "none",
            borderRadius: "0.75rem",
            fontWeight: "bold",
            fontSize: "1.1rem",
            cursor: "pointer",
            boxShadow: "0 4px 16px rgba(167,119,227,0.13)",
            marginBottom: "1.2rem",
            transition: "background 0.3s, box-shadow 0.2s",
          }}
          onMouseOver={(e) =>
            (e.target.style.background =
              "linear-gradient(90deg, #a777e3 0%, #6e8efb 100%)")
          }
          onMouseOut={(e) =>
            (e.target.style.background =
              "linear-gradient(90deg, #6e8efb 0%, #a777e3 100%)")
          }
        >
          Sign In
        </button>
        <div
          style={{
            textAlign: "center",
            fontSize: "1rem",
            color: "#888",
          }}
        >
          <span>Don't have an account? </span>
          <a
            href="/register"
            style={{
              color: "#a777e3",
              textDecoration: "underline",
              fontWeight: "bold",
            }}
          >
            Register
          </a>
        </div>
      </form>
      <footer
        style={{
          position: "absolute",
          bottom: 24,
          left: 0,
          width: "100%",
          textAlign: "center",
          color: "#fff",
          fontSize: "0.95rem",
          opacity: 0.7,
          zIndex: 1,
        }}
      >
        &copy; {new Date().getFullYear()} AdvisorAI. All rights reserved.
      </footer>
    </div>
  );
};

export default Login;
