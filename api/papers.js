export default function handler(request, response) {
  if (request.method === "GET") return response.status(200).json([]);
  return response.status(405).json({ detail: "Method not allowed" });
}
