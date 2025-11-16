export interface Message {
  role: "user" | "ai";
  content: string;
}

export interface Contacto {
  nombre: string;
  email: string;
  telefono: string;
  departamento: string;
}

export interface Reunion {
  id: string;
  titulo: string;
  dia: string;
  hora: string;
  invitados: string[];
  descripcion: string;
}

export interface Email {
  destinatario: string;
  asunto: string;
  contenido: string;
  fecha_envio: string;
}
