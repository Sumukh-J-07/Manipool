import React from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TextInputProps,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { ArrowLeft, ArrowUpRight, LucideIcon } from 'lucide-react-native';
import { colors as c, radius, typography as t } from '../theme';
import { Student } from '../types/domain';

export function Copy({
  children,
  muted,
  small,
  style,
}: React.PropsWithChildren<{
  muted?: boolean;
  small?: boolean;
  style?: import('react-native').StyleProp<import('react-native').TextStyle>;
}>) {
  return (
    <Text
      style={[styles.copy, muted && styles.muted, small && styles.small, style]}
    >
      {children}
    </Text>
  );
}
export function Heading({ children }: React.PropsWithChildren) {
  return (
    <Text accessibilityRole="header" style={styles.heading}>
      {children}
    </Text>
  );
}
export function Title({ children }: React.PropsWithChildren) {
  return (
    <Text accessibilityRole="header" style={styles.title}>
      {children}
    </Text>
  );
}
export function Kicker({ children }: React.PropsWithChildren) {
  return <Text style={styles.kicker}>{children}</Text>;
}
export function Page({
  children,
  back,
  label,
}: React.PropsWithChildren<{ back?: boolean; label?: string }>) {
  const navigation = useNavigation();
  return (
    <SafeAreaView
      edges={['top', 'bottom', 'left', 'right']}
      style={styles.page}
    >
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={styles.content}
        >
          {back && (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Go back"
              onPress={() => navigation.canGoBack() && navigation.goBack()}
              style={styles.back}
            >
              <ArrowLeft color={c.primary} size={22} />
              <Copy small>{label ?? 'Back'}</Copy>
            </Pressable>
          )}
          {children}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
export function Card({
  children,
  muted,
}: React.PropsWithChildren<{ muted?: boolean }>) {
  return (
    <View style={[styles.card, muted && styles.cardMuted]}>{children}</View>
  );
}
export function Row({
  children,
  wrap,
}: React.PropsWithChildren<{ wrap?: boolean }>) {
  return <View style={[styles.row, wrap && styles.wrap]}>{children}</View>;
}
export function Button({
  label,
  onPress,
  secondary,
  disabled,
  icon: Icon = ArrowUpRight,
}: {
  label: string;
  onPress: () => void;
  secondary?: boolean;
  disabled?: boolean;
  icon?: LucideIcon;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled: !!disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        secondary && styles.secondaryButton,
        (pressed || disabled) && styles.dim,
      ]}
    >
      <Text
        style={[styles.buttonText, secondary && styles.secondaryButtonText]}
      >
        {label}
      </Text>
      <Icon size={20} color={secondary ? c.primary : c.inverse} />
    </Pressable>
  );
}
export function Choice({
  label,
  detail,
  selected,
  onPress,
  icon: Icon,
  disabled,
}: {
  label: string;
  detail?: string;
  selected?: boolean;
  onPress: () => void;
  icon?: LucideIcon;
  disabled?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={[label, detail].filter(Boolean).join('. ')}
      accessibilityState={{ selected: !!selected, disabled: !!disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.choice,
        selected && styles.selected,
        (disabled || pressed) && styles.dim,
      ]}
    >
      {Icon && <Icon size={22} color={c.primary} />}
      <View style={styles.flex}>
        <Text style={styles.choiceText}>{label}</Text>
        {detail && (
          <Copy small muted>
            {detail}
          </Copy>
        )}
      </View>
      {selected && <Text style={styles.selectedLabel}>Selected</Text>}
    </Pressable>
  );
}
export function Input({ label, ...props }: TextInputProps & { label: string }) {
  return (
    <View style={styles.inputWrap}>
      <Copy small>{label}</Copy>
      <TextInput
        accessibilityLabel={label}
        placeholderTextColor={c.secondary}
        {...props}
        style={[styles.input, props.multiline && styles.multiline, props.style]}
      />
    </View>
  );
}
export function Notice({ children }: React.PropsWithChildren) {
  return (
    <View style={styles.notice}>
      <Copy small muted>
        {children}
      </Copy>
    </View>
  );
}
export function ErrorText({ message }: { message?: string }) {
  return message ? (
    <Text
      accessibilityRole="alert"
      accessibilityLiveRegion="polite"
      style={styles.error}
    >
      Please check: {message}
    </Text>
  ) : null;
}
export function Badge({ children }: React.PropsWithChildren) {
  return (
    <View style={styles.badge}>
      <Text style={styles.badgeText}>{children}</Text>
    </View>
  );
}
export function Avatar({ student }: { student: Student }) {
  return (
    <View accessibilityLabel={student.name} style={styles.avatar}>
      <Text style={styles.avatarText}>
        {student.name
          .trim()
          .split(/\s+/)
          .map(part => part[0])
          .slice(0, 2)
          .join('')}
      </Text>
    </View>
  );
}
export function Riders({
  members,
  detail = 'Demo student',
}: {
  members: Student[];
  detail?: string;
}) {
  return (
    <View style={styles.riders}>
      {members.map(member => (
        <Row key={member.id}>
          <Avatar student={member} />
          <View style={styles.flex}>
            <Copy>{member.name}</Copy>
            <Copy small muted>
              {member.area} · {detail}
            </Copy>
          </View>
        </Row>
      ))}
    </View>
  );
}
export const ui = StyleSheet.create({
  flex: { flex: 1 },
  gap: { gap: 12 },
  centered: { alignItems: 'center', gap: 16 },
  spread: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
  },
});
const styles = StyleSheet.create({
  flex: { flex: 1 },
  page: { flex: 1, backgroundColor: c.background },
  content: { padding: 24, paddingBottom: 40, gap: 20 },
  title: {
    color: c.text,
    fontSize: t.title,
    lineHeight: 39,
    fontWeight: '700',
    letterSpacing: -0.8,
  },
  heading: {
    color: c.text,
    fontSize: t.heading,
    lineHeight: 28,
    fontWeight: '600',
  },
  copy: { color: c.text, fontSize: t.body, lineHeight: 24 },
  muted: { color: c.secondary },
  small: { fontSize: t.secondary, lineHeight: 21 },
  kicker: {
    color: c.primary,
    fontSize: t.label,
    letterSpacing: 1.8,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  card: {
    backgroundColor: c.surface,
    borderWidth: 1,
    borderColor: c.border,
    borderRadius: radius.card,
    padding: 20,
    gap: 16,
  },
  cardMuted: { backgroundColor: c.surfaceMuted },
  row: { flexDirection: 'row', gap: 12, alignItems: 'center' },
  wrap: { flexWrap: 'wrap' },
  back: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    minHeight: 48,
    alignSelf: 'flex-start',
    paddingRight: 16,
  },
  button: {
    minHeight: 54,
    paddingVertical: 16,
    paddingHorizontal: 20,
    backgroundColor: c.primary,
    borderRadius: radius.control,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  buttonText: {
    color: c.inverse,
    fontSize: 16,
    fontWeight: '600',
    flexShrink: 1,
  },
  secondaryButton: {
    backgroundColor: c.background,
    borderColor: c.border,
    borderWidth: 1,
  },
  secondaryButtonText: { color: c.primary },
  dim: { opacity: 0.55 },
  choice: {
    borderWidth: 1,
    borderColor: c.border,
    backgroundColor: c.surface,
    borderRadius: radius.control,
    minHeight: 56,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  selected: { backgroundColor: c.surfaceMuted, borderColor: c.primary },
  choiceText: {
    fontSize: 16,
    lineHeight: 23,
    color: c.text,
    fontWeight: '500',
  },
  selectedLabel: { fontSize: 12, color: c.primary, fontWeight: '600' },
  inputWrap: { gap: 6 },
  input: {
    backgroundColor: c.surface,
    borderWidth: 1,
    borderColor: c.border,
    borderRadius: radius.control,
    padding: 16,
    minHeight: 54,
    color: c.text,
    fontSize: 16,
  },
  multiline: { minHeight: 110, textAlignVertical: 'top' },
  notice: { borderLeftWidth: 2, borderColor: c.accent, paddingLeft: 12 },
  error: { color: c.primary, lineHeight: 22, fontSize: 14, fontWeight: '600' },
  badge: {
    backgroundColor: c.surfaceMuted,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    alignSelf: 'flex-start',
  },
  badgeText: { color: c.primary, fontSize: 12, fontWeight: '600' },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: c.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { color: c.inverse, fontSize: 14, fontWeight: '600' },
  riders: { gap: 16 },
});
