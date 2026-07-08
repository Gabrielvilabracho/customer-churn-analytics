"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { TopRiskCustomerModel } from "./dashboard-model";

const SORT_COLUMNS = {
  CUSTOMER: "customer",
  RISK: "risk",
} as const;

const SORT_DIRECTIONS = {
  ASCENDING: "ascending",
  DESCENDING: "descending",
} as const;

type SortColumn = (typeof SORT_COLUMNS)[keyof typeof SORT_COLUMNS];
type SortDirection = (typeof SORT_DIRECTIONS)[keyof typeof SORT_DIRECTIONS];

interface SortState {
  column: SortColumn;
  direction: SortDirection;
}

interface RiskTableProps {
  customers: TopRiskCustomerModel[];
}

export function RiskTable({ customers }: RiskTableProps) {
  const [sortState, setSortState] = useState<SortState>({ column: SORT_COLUMNS.RISK, direction: SORT_DIRECTIONS.DESCENDING });

  if (customers.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Top-risk customers</CardTitle>
          <CardDescription>No customer risk rows are available.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const sortedCustomers = customers.toSorted((left, right) => compareCustomers(left, right, sortState));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Top-risk customers</CardTitle>
        <CardDescription>Sorted by predicted churn probability.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
                <th scope="col" aria-sort={ariaSortFor(SORT_COLUMNS.CUSTOMER, sortState)} className="py-3 pr-4">
                  <SortButton column={SORT_COLUMNS.CUSTOMER} sortState={sortState} onSort={setSortState}>Customer</SortButton>
                </th>
                <th scope="col" className="py-3 pr-4">Contract</th>
                <th scope="col" aria-sort={ariaSortFor(SORT_COLUMNS.RISK, sortState)} className="py-3 pr-4">
                  <SortButton column={SORT_COLUMNS.RISK} sortState={sortState} onSort={setSortState}>Risk</SortButton>
                </th>
                <th scope="col" className="py-3 pr-4">Payment</th>
                <th scope="col" className="py-3">Service</th>
              </tr>
            </thead>
            <tbody>
              {sortedCustomers.map((customer) => (
                <tr key={customer.sampleId} className="border-b last:border-b-0">
                  <td className="py-3 pr-4 font-medium">{customer.displayReference}</td>
                  <td className="py-3 pr-4">{customer.contract}</td>
                  <td className="py-3 pr-4">
                    <span className="inline-flex items-center gap-2">
                      <Badge variant={customer.riskLabel === "High risk" ? "default" : "secondary"}>{customer.riskLabel}</Badge>
                      <span>{customer.churnProbability}</span>
                    </span>
                  </td>
                  <td className="py-3 pr-4">{customer.paymentMethod}</td>
                  <td className="py-3">{customer.internetService}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function SortButton({ children, column, sortState, onSort }: { children: string; column: SortColumn; sortState: SortState; onSort: (state: SortState) => void }) {
  const nextDirection = sortState.column === column && sortState.direction === SORT_DIRECTIONS.DESCENDING ? SORT_DIRECTIONS.ASCENDING : SORT_DIRECTIONS.DESCENDING;

  return (
    <button
      type="button"
      className="inline-flex items-center gap-1 rounded-sm text-left font-medium focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
      aria-label={`Sort by ${children.toLowerCase()} ${nextDirection === SORT_DIRECTIONS.ASCENDING ? "ascending" : "descending"}`}
      onClick={() => onSort({ column, direction: nextDirection })}
    >
      {children}
      {sortState.column === column ? <span aria-hidden="true">{sortState.direction === SORT_DIRECTIONS.ASCENDING ? "↑" : "↓"}</span> : null}
    </button>
  );
}

function compareCustomers(left: TopRiskCustomerModel, right: TopRiskCustomerModel, sortState: SortState): number {
  const directionMultiplier = sortState.direction === SORT_DIRECTIONS.ASCENDING ? 1 : -1;

  if (sortState.column === SORT_COLUMNS.CUSTOMER) {
    return left.displayReference.localeCompare(right.displayReference) * directionMultiplier;
  }

  return (riskPercent(left.churnProbability) - riskPercent(right.churnProbability)) * directionMultiplier || left.displayReference.localeCompare(right.displayReference);
}

function riskPercent(value: string): number {
  return Number(value.replace("%", ""));
}

function ariaSortFor(column: SortColumn, sortState: SortState): SortDirection | "none" {
  return sortState.column === column ? sortState.direction : "none";
}
