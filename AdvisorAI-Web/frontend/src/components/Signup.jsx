import React, { useState } from "react";

const Signup = () => {
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError("");
    setSuccess("");
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.password || !form.confirmPassword) {
      setError("Please fill in all fields.");
      return;
    }
    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    
    setSuccess("Signup successful!");
    setForm({
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
    });
  };

  return (
    <div style={styles.container}>
      <form style={styles.form} onSubmit={handleSubmit}>
        <h2 style={styles.title}>Create Your Account</h2>
        <div style={styles.inputGroup}>
          <label style={styles.label}>Name</label>
          <input
            style={styles.input}
            type="text"
            name="name"
            value={form.name}
            onChange={handleChange}
            placeholder="Enter your name"
            autoComplete="off"
          />
        </div>
        <div style={styles.inputGroup}>
          <label style={styles.label}>Email</label>
          <input
            style={styles.input}
            type="email"
            name="email"
            value={form.email}
            onChange={handleChange}
            placeholder="Enter your email"
            autoComplete="off"
          />
        </div>
        <div style={styles.inputGroup}>
          <label style={styles.label}>Password</label>
          <input
            style={styles.input}
            type="password"
            name="password"
            value={form.password}
            onChange={handleChange}
            placeholder="Enter your password"
            autoComplete="new-password"
          />
        </div>
        <div style={styles.inputGroup}>
          <label style={styles.label}>Confirm Password</label>
          <input
            style={styles.input}
            type="password"
            name="confirmPassword"
            value={form.confirmPassword}
            onChange={handleChange}
            placeholder="Confirm your password"
            autoComplete="new-password"
          />
        </div>
        {error && <div style={styles.error}>{error}</div>}
        {success && <div style={styles.success}>{success}</div>}
        <button style={styles.button} type="submit">
          Sign Up
        </button>
        <div style={styles.footer}>
          Already have an account?{" "}
          <a href="/login" style={styles.link}>
            Login
          </a>
        </div>
      </form>
    </div>
  );
};

const styles = {
  container: {
    minHeight: "100vh",
    background: "linear-gradient(135deg, #6e8efb, #a777e3)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontFamily: "Segoe UI, Arial, sans-serif",
  },
  form: {
    background: "#fff",
    padding: "2.5rem 2rem",
    borderRadius: "18px",
    boxShadow: "0 8px 32px rgba(44, 62, 80, 0.15)",
    width: "100%",
    maxWidth: "400px",
    display: "flex",
    flexDirection: "column",
    gap: "1.2rem",
  },
  title: {
    marginBottom: "0.5rem",
    color: "#6e8efb",
    fontWeight: 700,
    fontSize: "2rem",
    textAlign: "center",
    letterSpacing: "1px",
  },
  inputGroup: {
    display: "flex",
    flexDirection: "column",
    gap: "0.3rem",
  },
  label: {
    fontSize: "1rem",
    color: "#444",
    fontWeight: 500,
  },
  input: {
    padding: "0.7rem",
    borderRadius: "8px",
    border: "1px solid #d1d5db",
    fontSize: "1rem",
    outline: "none",
    transition: "border 0.2s",
  },
  button: {
    padding: "0.8rem",
    borderRadius: "8px",
    border: "none",
    background: "linear-gradient(90deg, #6e8efb, #a777e3)",
    color: "#fff",
    fontWeight: 600,
    fontSize: "1.1rem",
    cursor: "pointer",
    marginTop: "0.5rem",
    boxShadow: "0 2px 8px rgba(44, 62, 80, 0.08)",
    transition: "background 0.2s",
  },
  error: {
    color: "#e74c3c",
    fontSize: "0.95rem",
    textAlign: "center",
    marginTop: "-0.5rem",
  },
  success: {
    color: "#27ae60",
    fontSize: "0.95rem",
    textAlign: "center",
    marginTop: "-0.5rem",
  },
  footer: {
    marginTop: "1rem",
    textAlign: "center",
    fontSize: "0.98rem",
    color: "#888",
  },
  link: {
    color: "#6e8efb",
    textDecoration: "none",
    fontWeight: 600,
  },
};

export default Signup;
