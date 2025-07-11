import { useState } from "react";
import reactLogo from "./assets/react.svg";
import { Route, Routes, NavLink } from "react-router-dom";
import Signup from "./components/Signup.jsx";
import Home from "./components/Home.jsx";
import Login from "./components/Login.jsx";
import "./App.css";

function App() {
  return (
    <div>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login />} />
      </Routes>
    </div>
  );
}

export default App;
