import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function MonitoringPage() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Monitoring</h2>
        <p className="text-muted-foreground">
          System performance and pipeline monitoring
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Pipeline Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[400px] bg-gray-100 dark:bg-gray-800 rounded-lg">
              {/* Pipeline status will go here */}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Logs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[400px] bg-gray-100 dark:bg-gray-800 rounded-lg">
              {/* System logs will go here */}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 