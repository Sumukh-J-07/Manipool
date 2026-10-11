import React from 'react';
import { View } from 'react-native';
import { CarpoolGroup, RideRequest } from '../types/domain';
import { Badge, Card, Copy, Heading, ui } from './ui';
import { dateLabel, money, splitFare, statusLabel } from '../services/journey';
import { vehicleOptions } from '../data/fixtures';
export function RideSummary({
  ride,
  group,
}: {
  ride: RideRequest;
  group?: CarpoolGroup;
}) {
  return (
    <Card>
      <Badge>{statusLabel(ride.status)}</Badge>
      <Heading>{ride.destination.name}</Heading>
      <Copy muted>
        {dateLabel(ride.departure)} ·{' '}
        {ride.flexibility ? `±${ride.flexibility} min` : 'Exact time'}
      </Copy>
      <Copy small>
        {ride.pickup.name} → {ride.destination.name}
      </Copy>
      {group && (
        <Copy small>
          {group.members.length} demo riders ·{' '}
          {group.pickupMode === 'common'
            ? 'Common meeting point'
            : 'Sequential pickups'}
        </Copy>
      )}
    </Card>
  );
}
export function FareBreakdown({ group }: { group: CarpoolGroup }) {
  const total = (group.booking?.option ?? vehicleOptions[0]).farePaise;
  const splits = splitFare(total, group.members.length);
  return (
    <Card>
      <View style={ui.spread}>
        <Heading>Suggested split</Heading>
        <Copy>{money(total)}</Copy>
      </View>
      {group.members.map((member, index) => (
        <View key={member.id} style={ui.spread}>
          <Copy small>{member.name}</Copy>
          <Copy>{money(splits[index])}</Copy>
        </View>
      ))}
      <Copy small muted>
        Illustrative total. Actual fares may differ; payment happens outside
        this demo.
      </Copy>
    </Card>
  );
}
