import { useState, useEffect } from "react";
import Chat from "./components/Chat";
import Contactos from "./components/Contactos";
import Reuniones from "./components/Reuniones";
import Emails from "./components/Emails";
import type { Contacto, Reunion, Email } from "./types/interfaces";

function App() {
  const [contactos, setContactos] = useState<Contacto[]>([]);
  const [reuniones, setReuniones] = useState<Reunion[]>([]);
  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(true);

  const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8001";

  const fetchData = async () => {
    try {
      const [contactosRes, reunionesRes, emailsRes] = await Promise.all([
        fetch(`${API_BASE}/contactos`),
        fetch(`${API_BASE}/reuniones`),
        fetch(`${API_BASE}/emails`),
      ]);

      const [contactosData, reunionesData, emailsData] = await Promise.all([
        contactosRes.json(),
        reunionesRes.json(),
        emailsRes.json(),
      ]);

      setContactos(contactosData);
      setReuniones(reunionesData);
      setEmails(emailsData);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleChatUpdate = () => {
    fetchData();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-800">
        <div className="text-xl text-gray-300">Cargando...</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-800">
      {/* Panel izquierdo - 40% */}
      <div className="w-2/5 flex flex-col gap-4 p-4 overflow-y-auto scroll-thin">
        <Contactos contactos={contactos} />
        <Reuniones reuniones={reuniones} />
        <Emails emails={emails} />
      </div>

      {/* Panel derecho - 60% */}
      <div className="w-3/5 p-4">
        <Chat onUpdate={handleChatUpdate} />
      </div>
    </div>
  );
}

export default App;
