import type { Reunion } from "../types/interfaces";

interface ReunionesProps {
  reuniones: Reunion[];
}

export default function Reuniones({ reuniones }: ReunionesProps) {
  return (
    <div className="bg-violet-100 rounded-lg shadow-md p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Reuniones</h3>
        <span className="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
          {reuniones.length}
        </span>
      </div>

      <div className="space-y-3 max-h-64 overflow-y-auto scroll-hide">
        {reuniones.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-4">
            No hay reuniones programadas
          </p>
        ) : (
          reuniones.map((reunion) => (
            <div
              key={reunion.id}
              className="border border-gray-200 rounded-lg p-3 bg-violet-200 hover:border-green-300 hover:bg-green-50 transition-all"
            >
              <h4 className="font-medium text-gray-900 mb-2">
                {reunion.titulo}
              </h4>

              <div className="flex items-center gap-2 text-sm text-gray-600 mb-1">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                <span>{reunion.dia}</span>
                <span className="mx-1">•</span>
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span>{reunion.hora}</span>
              </div>

              <p className="text-sm text-gray-600 mb-2">
                {reunion.descripcion}
              </p>

              <div className="flex items-center gap-1 text-sm text-gray-500">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                  />
                </svg>
                <span>{reunion.invitados.length} invitados</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
