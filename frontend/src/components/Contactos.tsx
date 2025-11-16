import type { Contacto } from "../types/interfaces";

interface ContactosProps {
  contactos: Contacto[];
}

export default function Contactos({ contactos }: ContactosProps) {
  return (
    <div className="bg-violet-100 rounded-lg shadow-md p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Contactos</h3>
        <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
          {contactos.length}
        </span>
      </div>

      <div className="space-y-3 max-h-64 overflow-y-auto scroll-hide">
        {contactos.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-4">
            No hay contactos registrados
          </p>
        ) : (
          contactos.map((contacto, idx) => (
            <div
              key={idx}
              className="border border-gray-200 rounded-lg p-3 bg-violet-200 hover:border-blue-300 hover:bg-blue-50 transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">
                    {contacto.nombre}
                  </h4>
                  <p className="text-sm text-gray-600 mt-1">{contacto.email}</p>
                  <p className="text-sm text-gray-600">{contacto.telefono}</p>
                </div>
                <span className="bg-purple-100 text-purple-800 text-xs font-medium px-2 py-1 rounded">
                  {contacto.departamento}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
