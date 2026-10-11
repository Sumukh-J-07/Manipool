import React, { useEffect, useRef } from 'react';
import { Animated, StyleSheet, View } from 'react-native';
import Svg, { Circle, Path, Rect } from 'react-native-svg';
import { colors as c } from '../theme';
import { Copy } from './ui';
export function RouteLogo({ inverse = false }: { inverse?: boolean }) {
  const color = inverse ? c.inverse : c.primary;
  return (
    <Svg
      width={52}
      height={52}
      viewBox="0 0 52 52"
      accessibilityLabel="Routes merging logo"
    >
      <Path
        d="M9 40 V12 Q9 7 14 12 L26 28 L38 12 Q43 7 43 12 V40 M26 28 V44"
        stroke={color}
        strokeWidth={3}
        strokeLinecap="round"
        fill="none"
      />
      <Circle cx={9} cy={40} r={3} fill={color} />
      <Circle cx={43} cy={40} r={3} fill={color} />
      <Circle cx={26} cy={44} r={3} fill={color} />
    </Svg>
  );
}
export function RouteMap({
  start = 'Campus area',
  end = 'Shared destination',
  animated = false,
  compact = false,
}: {
  start?: string;
  end?: string;
  animated?: boolean;
  compact?: boolean;
}) {
  const pulse = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    if (!animated) {
      return;
    }
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, {
          toValue: 0.4,
          duration: 650,
          useNativeDriver: true,
        }),
        Animated.timing(pulse, {
          toValue: 1,
          duration: 650,
          useNativeDriver: true,
        }),
      ]),
    );
    animation.start();
    return () => animation.stop();
  }, [animated, pulse]);
  return (
    <View
      style={styles.map}
      accessibilityLabel={`Demo route illustration from ${start} to ${end}. Multiple pickups merge into one route.`}
    >
      <Animated.View style={{ opacity: pulse }}>
        <Svg width="100%" height={compact ? 120 : 190} viewBox="0 0 320 190">
          <Rect width={320} height={190} fill={c.background} />
          <Path
            d="M0 45 H320 M0 140 H320 M65 0 V190 M245 0 V190 M0 185 L320 5"
            stroke={c.border}
            strokeWidth={7}
            fill="none"
          />
          <Path
            d="M34 44 C80 44 92 95 150 95 M40 149 C95 149 95 95 150 95"
            stroke={c.accent}
            strokeWidth={3}
            strokeDasharray="5 7"
            fill="none"
            strokeLinecap="round"
          />
          <Path
            d="M70 97 H152 Q180 97 198 70 T272 55"
            stroke={c.primary}
            strokeWidth={5}
            fill="none"
            strokeLinecap="round"
          />
          {[
            { x: 34, y: 44 },
            { x: 40, y: 149 },
            { x: 70, y: 97 },
          ].map(point => (
            <Circle
              key={point.y}
              cx={point.x}
              cy={point.y}
              r={7}
              fill={c.surface}
              stroke={c.accent}
              strokeWidth={3}
            />
          ))}
          <Circle cx={152} cy={97} r={9} fill={c.primary} />
          <Circle cx={272} cy={55} r={12} fill={c.primaryDark} />
          <Circle cx={272} cy={55} r={4} fill={c.inverse} />
        </Svg>
      </Animated.View>
      <View style={styles.labels}>
        <Copy small>{start}</Copy>
        <Copy small>{end}</Copy>
      </View>
      <Copy small muted>
        Schematic route · demo locations
      </Copy>
    </View>
  );
}
const styles = StyleSheet.create({
  map: {
    backgroundColor: c.background,
    borderRadius: 16,
    padding: 12,
    gap: 8,
    overflow: 'hidden',
  },
  labels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
    flexWrap: 'wrap',
  },
});
