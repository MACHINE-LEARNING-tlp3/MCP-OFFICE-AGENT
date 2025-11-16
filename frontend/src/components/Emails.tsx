import type { Email } from "../types/interfaces";

interface EmailsProps {
  emails: Email[];
}

export default function Emails({ emails }: EmailsProps) {
  return (
    <div className="bg-violet-100 rounded-lg shadow-md p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Emails</h3>
        <span className="bg-orange-100 text-orange-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
          {emails.length}
        </span>
      </div>

      <div className="space-y-3 max-h-64 overflow-y-auto scroll-hide">
        {emails.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-4">
            No hay emails enviados
          </p>
        ) : (
          emails.map((email, idx) => (
            <div
              key={idx}
              className="border border-gray-200 rounded-lg p-3 bg-violet-200 hover:border-orange-300 hover:bg-orange-50 transition-all"
            >
              <div className="flex items-start gap-2 mb-2">
                <svg
                  className="w-4 h-4 mt-0.5 text-gray-500 shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
                <div className="flex-1">
                  <p className="font-medium text-gray-900 text-sm">
                    {email.destinatario}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {email.fecha_envio}
                  </p>
                </div>
              </div>

              <h4 className="font-medium text-gray-800 text-sm mb-1">
                {email.asunto}
              </h4>
              <p className="text-sm text-gray-600 line-clamp-2">
                {email.contenido}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
