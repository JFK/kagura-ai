/**
 * Health check endpoint for Docker health checks
 */
export async function GET() {
  return Response.json(
    { status: 'ok', timestamp: new Date().toISOString() },
    { status: 200 }
  );
}
