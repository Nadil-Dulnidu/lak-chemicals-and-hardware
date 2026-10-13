"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkles, TrendingUp, CheckCircle2, AlertTriangle, Lightbulb } from "lucide-react";
import { AiReportAnalysis } from "@/lib/types";

interface AiAnalysisCardProps {
  analysis: AiReportAnalysis;
  reportType?: string;
}

export function AiAnalysisCard({ analysis, reportType }: AiAnalysisCardProps) {
  if (!analysis) return null;

  return (
    <Card className="border-orange-500/30 bg-gradient-to-br from-orange-500/5 via-card to-amber-500/5 shadow-lg overflow-hidden">
      <CardHeader className="border-b border-border/50 pb-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-orange-500/10 text-orange-500">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-lg font-bold flex items-center gap-2 text-foreground">
                Gemini 2.5 Pro Executive Analysis
                <Badge variant="outline" className="border-orange-500/40 text-orange-400 text-xs font-normal">
                  Express Mode
                </Badge>
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Autonomous business intelligence & management recommendations
              </CardDescription>
            </div>
          </div>
          {reportType && (
            <Badge className="bg-orange-500/20 text-orange-400 hover:bg-orange-500/30 uppercase tracking-wider text-xs">
              {reportType.replace("-", " ")}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="pt-6 space-y-6">
        {/* Executive Summary */}
        <div className="p-4 rounded-xl bg-background/80 border border-border/60 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground mb-2">
            <Lightbulb className="h-4 w-4 text-amber-400" />
            Executive Summary
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {analysis.summary}
          </p>
        </div>

        {/* Risk Alerts (if any) */}
        {analysis.risk_alerts && analysis.risk_alerts.length > 0 && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30">
            <div className="flex items-center gap-2 text-sm font-semibold text-red-400 mb-2">
              <AlertTriangle className="h-4 w-4 text-red-400" />
              Critical Risk Alerts
            </div>
            <ul className="space-y-1.5 text-sm text-red-300">
              {analysis.risk_alerts.map((alert, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-red-400 font-bold">•</span>
                  <span>{alert}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Key Insights */}
          {analysis.insights && analysis.insights.length > 0 && (
            <div className="p-4 rounded-xl bg-card border border-border/60 space-y-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                <TrendingUp className="h-4 w-4 text-blue-400" />
                Key Trends & Performance Insights
              </div>
              <ul className="space-y-2 text-sm text-muted-foreground">
                {analysis.insights.map((insight, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-blue-400 font-bold">•</span>
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Actionable Recommendations */}
          {analysis.recommendations && analysis.recommendations.length > 0 && (
            <div className="p-4 rounded-xl bg-card border border-border/60 space-y-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                Actionable Management Recommendations
              </div>
              <ul className="space-y-2 text-sm text-muted-foreground">
                {analysis.recommendations.map((rec, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">✓</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
