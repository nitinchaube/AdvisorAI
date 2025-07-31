import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiService } from "../services/api";
import {
  User,
  Mail,
  MapPin,
  Star,
  Briefcase,
  GraduationCap,
  Award,
  Target,
  Github,
  Linkedin,
} from "lucide-react";
import ReactDOM from "react-dom";

// Helper for avatar initials
const getInitials = (name) => {
  if (!name) return "?";
  const parts = name.split(" ");
  return parts.length === 1
    ? parts[0][0].toUpperCase()
    : (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
};

// SVG blob for creative backgrounds
const Blob = ({ style, color }) => (
  <svg
    viewBox="0 0 200 200"
    width="340"
    height="340"
    style={{ position: "absolute", ...style }}
  >
    <path
      fill={color || "#38bdf8"}
      d="M44.8,-67.2C56.7,-59.7,63.7,-44.2,68.2,-29.2C72.7,-14.2,74.7,0.3,70.2,13.2C65.7,26.1,54.7,37.4,42.1,46.2C29.5,55,15.2,61.3,0.2,61.1C-14.8,60.9,-29.6,54.2,-41.2,44.7C-52.8,35.2,-61.2,23,-66.2,8.7C-71.2,-5.6,-72.8,-22,-65.7,-34.7C-58.6,-47.4,-42.8,-56.4,-27.1,-62.7C-11.4,-69,4.2,-72.6,19.2,-71.1C34.2,-69.6,49.6,-63.7,44.8,-67.2Z"
      transform="translate(100 100)"
    />
  </svg>
);

// Hero/Intro Section
const Hero = ({
  name,
  tagline,
  avatarInitials,
  location,
  email,
  github,
  linkedin,
}) => (
  <section
    style={{
      position: "relative",
      minHeight: 340,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      textAlign: "center",
      padding: "3.5rem 1rem 2rem 1rem",
      overflow: "hidden",
      zIndex: 1,
    }}
  >
    <Blob
      style={{ top: -60, left: -80, zIndex: 0, opacity: 0.18 }}
      color="#38bdf8"
    />
    <Blob
      style={{ bottom: -80, right: -100, zIndex: 0, opacity: 0.13 }}
      color="#06b6d4"
    />
    <div
      style={{
        width: 120,
        height: 120,
        borderRadius: "50%",
        background: "linear-gradient(135deg, #06b6d4 0%, #38bdf8 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "3.2rem",
        fontWeight: 800,
        color: "#fff",
        boxShadow: "0 4px 24px rgba(6,182,212,0.18)",
        marginBottom: 18,
        letterSpacing: "0.04em",
        textTransform: "uppercase",
        userSelect: "none",
        zIndex: 1,
        animation: "popIn 0.8s cubic-bezier(.68,-0.55,.27,1.55)",
      }}
    >
      {avatarInitials}
    </div>
    <h1
      style={{
        fontSize: "2.7rem",
        fontWeight: 900,
        margin: 0,
        color: "#0f172a",
        zIndex: 1,
        letterSpacing: "0.01em",
        animation: "fadeIn 1.2s",
      }}
    >
      Hi, I’m {name}{" "}
      <span role="img" aria-label="wave">
        👋
      </span>
    </h1>
    <div
      style={{
        fontSize: "1.3rem",
        color: "#06b6d4",
        fontWeight: 600,
        margin: "0.7rem 0 0.5rem 0",
        zIndex: 1,
        animation: "fadeIn 1.5s",
      }}
    >
      {tagline}
    </div>
    <div
      style={{
        display: "flex",
        gap: "1.2rem",
        justifyContent: "center",
        margin: "1.2rem 0",
        zIndex: 1,
      }}
    >
      {location && (
        <span
          style={{
            display: "flex",
            alignItems: "center",
            color: "#334155",
            fontWeight: 500,
          }}
        >
          <MapPin style={{ width: 18, marginRight: 4 }} />
          {location}
        </span>
      )}
      {email && (
        <span
          style={{
            display: "flex",
            alignItems: "center",
            color: "#334155",
            fontWeight: 500,
          }}
        >
          <Mail style={{ width: 18, marginRight: 4 }} />
          {email}
        </span>
      )}
      {github && (
        <a
          href={github}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: "#0f172a" }}
        >
          <Github style={{ width: 20 }} />
        </a>
      )}
      {linkedin && (
        <a
          href={linkedin}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: "#0f172a" }}
        >
          <Linkedin style={{ width: 20 }} />
        </a>
      )}
    </div>
    <style>{`
      @keyframes popIn { 0% { transform: scale(0.7); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
      @keyframes fadeIn { 0% { opacity: 0; } 100% { opacity: 1; } }
    `}</style>
  </section>
);

// Story/About Section
const Story = ({ summary }) => (
  <section
    style={{
      maxWidth: 700,
      margin: "0 auto",
      marginTop: 24,
      marginBottom: 36,
      background: "rgba(255,255,255,0.8)",
      borderRadius: 18,
      boxShadow: "0 2px 16px rgba(6,182,212,0.08)",
      padding: "2.2rem 2rem",
      fontSize: "1.18rem",
      color: "#0f172a",
      fontWeight: 500,
      lineHeight: 1.7,
      textAlign: "center",
      position: "relative",
      zIndex: 2,
      animation: "fadeInUp 1.1s",
    }}
  >
    <span
      style={{
        fontWeight: 700,
        color: "#06b6d4",
        fontSize: "1.2rem",
        letterSpacing: "0.01em",
      }}
    >
      My Story
    </span>
    <div style={{ marginTop: 10 }}>{summary}</div>
    <style>{`
      @keyframes fadeInUp { 0% { opacity: 0; transform: translateY(40px); } 100% { opacity: 1; transform: translateY(0); } }
    `}</style>
  </section>
);

// Skills Cloud
const SkillsCloud = ({ skills }) => (
  <section
    style={{
      maxWidth: 900,
      margin: "0 auto",
      marginBottom: 36,
      display: "flex",
      flexWrap: "wrap",
      justifyContent: "center",
      gap: "1.1rem",
      position: "relative",
      zIndex: 2,
      animation: "fadeInUp 1.2s",
    }}
  >
    {skills.map((skill, idx) => (
      <span
        key={idx}
        style={{
          display: "inline-block",
          background: `linear-gradient(90deg, #06b6d4 0%, #38bdf8 100%)`,
          color: "#fff",
          borderRadius: 999,
          padding: "0.7em 1.5em",
          fontWeight: 700,
          fontSize: "1.08rem",
          boxShadow: "0 2px 8px rgba(6,182,212,0.10)",
          letterSpacing: "0.01em",
          transform: `rotate(${
            (idx % 2 === 0 ? 1 : -1) * (5 + (idx % 3) * 2)
          }deg) scale(${1 + (idx % 4) * 0.03})`,
          transition: "transform 0.2s",
          cursor: "pointer",
          animation: `popInSkill 0.7s ${0.2 + idx * 0.07}s both`,
        }}
      >
        {skill}
      </span>
    ))}
    <style>{`
      @keyframes popInSkill { 0% { opacity: 0; transform: scale(0.7) translateY(30px); } 100% { opacity: 1; transform: scale(1) translateY(0); } }
    `}</style>
  </section>
);

// Horizontal Experience Timeline with modal for details
const HorizontalTimeline = ({ items }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState({});

  const openModal = (item) => {
    setModalContent(item);
    setModalOpen(true);
  };
  const closeModal = () => setModalOpen(false);

  // Modal JSX
  const modalJSX = modalOpen ? (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        background: "rgba(30,41,59,0.35)",
        backdropFilter: "blur(2px)",
        WebkitBackdropFilter: "blur(2px)",
        zIndex: 99999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
      onClick={closeModal}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: 16,
          maxWidth: 440,
          width: "92vw",
          padding: "2.2rem 1.7rem",
          boxShadow: "0 8px 32px rgba(6,182,212,0.18)",
          position: "relative",
          animation: "fadeInModal 0.3s",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            fontWeight: 800,
            fontSize: "1.18rem",
            color: "#0f172a",
            marginBottom: 6,
          }}
        >
          {modalContent.title || modalContent.position || "-"}
        </div>
        {modalContent.company &&
          (modalContent.companyUrl ? (
            <a
              href={modalContent.companyUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                color: "#06b6d4",
                fontWeight: 700,
                marginBottom: 2,
                textDecoration: "underline",
                fontSize: "1.05rem",
              }}
            >
              {modalContent.company}
            </a>
          ) : (
            <div
              style={{
                color: "#06b6d4",
                fontWeight: 700,
                marginBottom: 2,
                fontSize: "1.05rem",
              }}
            >
              {modalContent.company}
            </div>
          ))}
        {(modalContent.period ||
          modalContent.duration ||
          modalContent.startDate) && (
          <div
            style={{
              color: "#38bdf8",
              fontSize: "0.99rem",
              marginBottom: 10,
              fontWeight: 500,
            }}
          >
            {modalContent.period ||
              modalContent.duration ||
              `${modalContent.startDate || ""}${
                modalContent.endDate ? " - " + modalContent.endDate : ""
              }`}
          </div>
        )}
        <div
          style={{
            color: "#334155",
            opacity: 0.98,
            marginTop: 2,
            whiteSpace: "pre-line",
            fontSize: "1.04rem",
            fontWeight: 500,
          }}
        >
          {modalContent.description}
        </div>
        <button
          style={{
            marginTop: 18,
            background: "linear-gradient(90deg, #38bdf8 0%, #06b6d4 100%)",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            padding: "0.4rem 1.1rem",
            fontWeight: 600,
            fontSize: "0.98rem",
            cursor: "pointer",
            boxShadow: "0 2px 8px rgba(6,182,212,0.10)",
            transition: "background 0.18s",
            position: "absolute",
            right: 18,
            bottom: 18,
          }}
          onClick={closeModal}
        >
          Close
        </button>
      </div>
      <style>{`
        @keyframes fadeInModal { 0% { opacity: 0; transform: scale(0.95); } 100% { opacity: 1; transform: scale(1); } }
      `}</style>
    </div>
  ) : null;

  return (
    <>
      <section
        style={{
          maxWidth: 1200,
          margin: "0 auto",
          marginBottom: 56,
          position: "relative",
          zIndex: 2,
        }}
      >
        <h2
          style={{
            textAlign: "center",
            color: "#06b6d4",
            fontWeight: 800,
            fontSize: "1.6rem",
            marginBottom: 36,
            letterSpacing: "0.01em",
          }}
        >
          Experience
        </h2>
        <div
          style={{
            overflowX: "auto",
            paddingBottom: 48,
            margin: "0 -1.5rem",
            WebkitOverflowScrolling: "touch",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "flex-end",
              gap: 48,
              minWidth: 600,
              padding: "0 2rem",
              position: "relative",
            }}
          >
            {/* Timeline line */}
            <div
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                bottom: 0,
                height: 4,
                background: "linear-gradient(90deg, #38bdf8 0%, #06b6d4 100%)",
                opacity: 0.18,
                zIndex: 0,
              }}
            />
            {items.map((item, idx) => {
              // Truncate description to 2 lines
              const shortDesc =
                item.description && item.description.length > 0
                  ? item.description.split(" ").slice(0, 20).join(" ") +
                    (item.description.split(" ").length > 20 ? "..." : "")
                  : "";
              // Company as link if item.companyUrl exists
              const companyLink =
                item.companyUrl ||
                (item.company && item.company.toLowerCase().includes("http")
                  ? item.company
                  : null);
              return (
                <div
                  key={idx}
                  tabIndex={0}
                  role="button"
                  aria-label="View experience details"
                  onClick={() => openModal(item)}
                  onKeyDown={(e) =>
                    (e.key === "Enter" || e.key === " ") && openModal(item)
                  }
                  style={{
                    position: "relative",
                    zIndex: 2,
                    minWidth: 300,
                    maxWidth: 300,
                    flex: "0 0 300px",
                    background: "rgba(255,255,255,0.97)",
                    borderRadius: 18,
                    boxShadow: "0 2px 16px rgba(6,182,212,0.10)",
                    border: "2.5px solid #38bdf8",
                    padding: "1.5rem 1.7rem 2.5rem 1.7rem",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "flex-start",
                    transition:
                      "transform 0.18s, box-shadow 0.18s, border-color 0.18s",
                    cursor: "pointer",
                    animation: `fadeInUp 0.9s ${0.2 + idx * 0.11}s both`,
                    outline: "none",
                    boxSizing: "border-box",
                    userSelect: "none",
                    borderBottom: "4px solid transparent",
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.boxShadow =
                      "0 8px 32px rgba(6,182,212,0.18)";
                    e.currentTarget.style.transform = "scale(1.035)";
                    e.currentTarget.style.borderColor = "#06b6d4";
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.boxShadow =
                      "0 2px 16px rgba(6,182,212,0.10)";
                    e.currentTarget.style.transform = "scale(1)";
                    e.currentTarget.style.borderColor = "#38bdf8";
                  }}
                >
                  <div
                    style={{
                      fontWeight: 800,
                      fontSize: "1.18rem",
                      color: "#0f172a",
                      marginBottom: 6,
                      letterSpacing: "0.01em",
                    }}
                  >
                    {item.title || item.position || "-"}
                  </div>
                  {item.company &&
                    (companyLink ? (
                      <a
                        href={companyLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          color: "#06b6d4",
                          fontWeight: 700,
                          marginBottom: 2,
                          textDecoration: "underline",
                          fontSize: "1.05rem",
                        }}
                      >
                        {item.company}
                      </a>
                    ) : (
                      <div
                        style={{
                          color: "#06b6d4",
                          fontWeight: 700,
                          marginBottom: 2,
                          fontSize: "1.05rem",
                        }}
                      >
                        {item.company}
                      </div>
                    ))}
                  {(item.period || item.duration || item.startDate) && (
                    <div
                      style={{
                        color: "#38bdf8",
                        fontSize: "0.99rem",
                        marginBottom: 8,
                        fontWeight: 500,
                      }}
                    >
                      {item.period ||
                        item.duration ||
                        `${item.startDate || ""}${
                          item.endDate ? " - " + item.endDate : ""
                        }`}
                    </div>
                  )}
                  {item.description && (
                    <div
                      style={{
                        color: "#334155",
                        opacity: 0.92,
                        marginTop: 2,
                        minHeight: 44,
                        maxHeight: 44,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        display: "-webkit-box",
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: "vertical",
                        fontSize: "1.01rem",
                        fontWeight: 500,
                      }}
                    >
                      {shortDesc}
                    </div>
                  )}
                  {/* Timeline dot */}
                  <div
                    style={{
                      position: "absolute",
                      left: "50%",
                      bottom: -28,
                      transform: "translateX(-50%)",
                      width: 20,
                      height: 20,
                      background:
                        "linear-gradient(135deg, #38bdf8 0%, #06b6d4 100%)",
                      borderRadius: "50%",
                      border: "3px solid #fff",
                      boxShadow: "0 2px 8px rgba(6,182,212,0.10)",
                      zIndex: 3,
                    }}
                  />
                </div>
              );
            })}
          </div>
        </div>
      </section>
      {modalOpen && ReactDOM.createPortal(modalJSX, document.body)}
      <style>{`
        @keyframes fadeInUp { 0% { opacity: 0; transform: translateY(40px); } 100% { opacity: 1; transform: translateY(0); } }
        @media (max-width: 700px) {
          .exp-card { min-width: 220px !important; max-width: 90vw !important; }
        }
      `}</style>
    </>
  );
};

// Projects Gallery
const ProjectsGallery = ({ projects }) => (
  <section
    style={{
      maxWidth: 1000,
      margin: "0 auto",
      marginBottom: 36,
      zIndex: 2,
      position: "relative",
    }}
  >
    <h2
      style={{
        textAlign: "center",
        color: "#38bdf8",
        fontWeight: 800,
        fontSize: "1.4rem",
        marginBottom: 30,
        letterSpacing: "0.01em",
      }}
    >
      Projects
    </h2>
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "1.5rem",
        justifyContent: "center",
      }}
    >
      {projects.map((proj, idx) => (
        <div
          key={idx}
          style={{
            background: "rgba(255,255,255,0.97)",
            borderRadius: 18,
            boxShadow: "0 2px 16px rgba(6,182,212,0.10)",
            padding: "1.2rem 1.2rem",
            minWidth: 220,
            maxWidth: 320,
            flex: "1 1 220px",
            border: "2.5px solid #06b6d4",
            position: "relative",
            transition: "transform 0.18s",
            cursor: "pointer",
            animation: `fadeInUp 0.9s ${0.2 + idx * 0.11}s both`,
          }}
        >
          <div
            style={{ fontWeight: 700, fontSize: "1.13rem", color: "#0f172a" }}
          >
            {proj.name || proj.title || "-"}
          </div>
          {proj.date && (
            <div style={{ color: "#06b6d4", fontWeight: 600 }}>{proj.date}</div>
          )}
          {proj.description && (
            <div style={{ color: "#0f172a", opacity: 0.85, marginTop: 6 }}>
              {proj.description}
            </div>
          )}
        </div>
      ))}
    </div>
    <style>{`
      @keyframes fadeInUp { 0% { opacity: 0; transform: translateY(40px); } 100% { opacity: 1; transform: translateY(0); } }
    `}</style>
  </section>
);

// Education Badges
const EducationBadges = ({ education }) => (
  <section
    style={{
      maxWidth: 900,
      margin: "0 auto",
      marginBottom: 36,
      display: "flex",
      flexWrap: "wrap",
      gap: "1.2rem",
      justifyContent: "center",
      zIndex: 2,
      position: "relative",
    }}
  >
    {education.map((edu, idx) => (
      <div
        key={idx}
        style={{
          background: "linear-gradient(135deg, #38bdf8 0%, #06b6d4 100%)",
          color: "#fff",
          borderRadius: 16,
          boxShadow: "0 2px 16px rgba(6,182,212,0.10)",
          padding: "1.1rem 1.5rem",
          minWidth: 180,
          maxWidth: 320,
          fontWeight: 700,
          fontSize: "1.08rem",
          textAlign: "center",
          animation: `fadeInUp 0.9s ${0.2 + idx * 0.09}s both`,
        }}
      >
        <GraduationCap style={{ width: 22, height: 22, marginBottom: 6 }} />
        <div>{edu.degree || edu.title || "-"}</div>
        {edu.institution && (
          <div style={{ color: "#0f172a", fontWeight: 600 }}>
            {edu.institution}
          </div>
        )}
        {(edu.period || edu.duration || edu.startDate) && (
          <div style={{ color: "#fff", fontSize: "0.97rem", marginTop: 2 }}>
            {edu.period ||
              edu.duration ||
              `${edu.startDate || ""}${edu.endDate ? " - " + edu.endDate : ""}`}
          </div>
        )}
      </div>
    ))}
    <style>{`
      @keyframes fadeInUp { 0% { opacity: 0; transform: translateY(40px); } 100% { opacity: 1; transform: translateY(0); } }
    `}</style>
  </section>
);

const PortfolioView = () => {
  const { userId } = useParams();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      setError("");
      try {
        const res = await apiService.getPublicProfile(userId);
        if (res.success && res.profile) {
          setProfile(res.profile);
        } else {
          setError("Profile not found or not public.");
        }
      } catch (e) {
        setError("Failed to load portfolio.");
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [userId]);

  if (loading)
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "linear-gradient(135deg, #e0fdfa 0%, #38bdf8 100%)",
          color: "#06b6d4",
        }}
      >
        <div style={{ fontSize: "2rem" }}>Loading portfolio...</div>
      </div>
    );
  if (error)
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "linear-gradient(135deg, #e0fdfa 0%, #38bdf8 100%)",
          color: "#ef4444",
        }}
      >
        <div style={{ fontSize: "1.5rem" }}>{error}</div>
      </div>
    );
  if (!profile) return null;

  // Tagline: use summary first sentence or fallback
  const tagline = profile.summary
    ? profile.summary.split(". ")[0] + "."
    : "Turning ideas into impact.";
  // Socials: try to extract from profile if available
  const github = profile.github || (profile.socials && profile.socials.github);
  const linkedin =
    profile.linkedin || (profile.socials && profile.socials.linkedin);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #e0fdfa 0%, #38bdf8 100%)",
        color: "#0f172a",
        fontFamily: "Inter, sans-serif",
        overflow: "auto",
        boxSizing: "border-box",
        position: "relative",
      }}
    >
      {/* Hero/Intro */}
      <Hero
        name={profile.fullName}
        tagline={tagline}
        avatarInitials={getInitials(profile.fullName)}
        location={profile.location}
        email={profile.email}
        github={github}
        linkedin={linkedin}
      />
      {/* Story/About */}
      {profile.summary && <Story summary={profile.summary} />}
      {/* Experience Timeline */}
      {profile.experience &&
        Array.isArray(profile.experience) &&
        profile.experience.length > 0 && (
          <HorizontalTimeline items={profile.experience} />
        )}
      {/* Projects Gallery */}
      {profile.projects &&
        Array.isArray(profile.projects) &&
        profile.projects.length > 0 && (
          <ProjectsGallery projects={profile.projects} />
        )}
      {/* Skills Cloud */}
      {profile.skills &&
        Array.isArray(profile.skills) &&
        profile.skills.length > 0 && <SkillsCloud skills={profile.skills} />}
      {/* Education Badges */}
      {profile.education &&
        Array.isArray(profile.education) &&
        profile.education.length > 0 && (
          <EducationBadges education={profile.education} />
        )}
      {/* Footer */}
      <footer
        style={{
          width: "100%",
          padding: "2.5rem 0 1.5rem 0",
          background: "linear-gradient(135deg, #38bdf8 0%, #06b6d4 100%)",
          color: "#fff",
          textAlign: "center",
          fontWeight: 600,
          fontSize: "1.1rem",
          letterSpacing: "0.01em",
          marginTop: 40,
          position: "relative",
          zIndex: 2,
        }}
      >
        <div>Let’s Connect!</div>
        <div
          style={{
            marginTop: 10,
            display: "flex",
            justifyContent: "center",
            gap: 18,
          }}
        >
          {profile.email && (
            <a href={`mailto:${profile.email}`} style={{ color: "#fff" }}>
              <Mail style={{ width: 22 }} />
            </a>
          )}
          {github && (
            <a
              href={github}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#fff" }}
            >
              <Github style={{ width: 22 }} />
            </a>
          )}
          {linkedin && (
            <a
              href={linkedin}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#fff" }}
            >
              <Linkedin style={{ width: 22 }} />
            </a>
          )}
        </div>
        <div style={{ marginTop: 18, fontSize: "0.98rem", opacity: 0.8 }}>
          © {new Date().getFullYear()} {profile.fullName}
        </div>
      </footer>
    </div>
  );
};

export default PortfolioView;
