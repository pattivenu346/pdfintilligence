export default function handler(_request, response) {
  response.status(503).json({
    detail: "Cloud storage is not configured yet. Add Vercel Blob and a database before processing uploads in production."
  });
}
