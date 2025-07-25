import React, { useEffect, useState } from "react";
import { getFirestore, collection, getDocs } from "firebase/firestore";
import { app } from "./firebase"; // adjust path if needed

const db = getFirestore(app);

function FacultyExplorer() {
  const [faculty, setFaculty] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchFaculty() {
      try {
        const facultyCol = collection(db, "faculty"); // assumes collection is named 'faculty'
        const facultySnapshot = await getDocs(facultyCol);
        const facultyList = facultySnapshot.docs.map(doc => ({
          id: doc.id,
          ...doc.data(),
        }));
        setFaculty(facultyList);
      } catch (error) {
        console.error("Error fetching faculty data:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchFaculty();
  }, []);

  if (loading) return <div>Loading faculty data...</div>;

  return (
    <div>
      <h2>Faculty Explorer</h2>
      {faculty.length === 0 ? (
        <div>No faculty found.</div>
      ) : (
        <ul>
          {faculty.map(f => (
            <li key={f.id}>
              <h3>{f.name}</h3>
              <p>{f.general_info}</p>
              <p>{f.research_info}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default FacultyExplorer;