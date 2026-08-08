export default function handler(_request, response) {
  response.status(200).json({
    totalPapers: 0, subjects: 0, departments: 0, years: 0,
    storageBytes: 0, recent: []
  });
}
