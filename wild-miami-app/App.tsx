import { StatusBar } from 'expo-status-bar';
import * as ImagePicker from 'expo-image-picker';
import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Image, Linking, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { AppDb, getIncidentOptions, getSpecies, getUserVersion, openAppDb } from './src/db';
import { identifyWithFixtureModel } from './src/scoring';
import { IncidentOption, Result, Species } from './src/types';

type Screen = 'home' | 'result' | 'incidents' | 'error';

export default function App() {
  const [db, setDb] = useState<AppDb | null>(null);
  const [species, setSpecies] = useState<Species[]>([]);
  const [userVersion, setUserVersion] = useState(0);
  const [screen, setScreen] = useState<Screen>('home');
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [incidentOptions, setIncidentOptions] = useState<IncidentOption[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function boot() {
      try {
        const openedDb = await openAppDb();
        const [loadedSpecies, version] = await Promise.all([getSpecies(openedDb), getUserVersion(openedDb)]);
        if (!mounted) return;
        setDb(openedDb);
        setSpecies(loadedSpecies);
        setUserVersion(version);
      } catch (bootError) {
        if (!mounted) return;
        setError(bootError instanceof Error ? bootError.message : 'Unable to open the wildlife database.');
        setScreen('error');
      } finally {
        if (mounted) setLoading(false);
      }
    }
    boot();
    return () => {
      mounted = false;
    };
  }, []);

  const speciesById = useMemo(() => new Map(species.map((item) => [item.id, item])), [species]);
  const topSpecies = result?.matches[0] ? speciesById.get(result.matches[0].speciesId) : null;
  const isFixture = userVersion === 0;

  async function takePhoto() {
    try {
      const permission = await ImagePicker.requestCameraPermissionsAsync();
      if (!permission.granted) {
        setError('Camera permission was denied. This is the visible failure state; use gallery or Demo/FIXTURE mode, or grant permission.');
        setScreen('error');
        return;
      }
      const picked = await ImagePicker.launchCameraAsync({ mediaTypes: ['images'], quality: 0.85 });
      if (picked.canceled) return;
      runFixtureIdentifier(picked.assets[0]?.uri ?? 'camera-fixture');
    } catch (cameraError) {
      setError(cameraError instanceof Error ? cameraError.message : 'Could not open the camera.');
      setScreen('error');
    }
  }

  async function pickImage() {
    try {
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permission.granted) {
        setError('Gallery permission was denied. This is the visible failure state; use Camera or Demo/FIXTURE mode, or grant permission.');
        setScreen('error');
        return;
      }
      const picked = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], quality: 0.85 });
      if (picked.canceled) return;
      runFixtureIdentifier(picked.assets[0]?.uri ?? 'gallery-fixture');
    } catch (pickError) {
      setError(pickError instanceof Error ? pickError.message : 'Could not select an image.');
      setScreen('error');
    }
  }

  function runFixtureIdentifier(uri: string) {
    setPhotoUri(uri);
    setResult(identifyWithFixtureModel(uri, species));
    setScreen('result');
  }

  async function openIncidentPicker(targetSpecies: Species) {
    if (!db) return;
    const options = await getIncidentOptions(db, targetSpecies.id);
    setIncidentOptions(options);
    setScreen('incidents');
  }

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator />
        <Text style={styles.muted}>Opening fixture database…</Text>
      </View>
    );
  }

  return (
    <View style={styles.root}>
      <StatusBar style="dark" />
      {isFixture ? <Text style={styles.fixtureBanner}>FIXTURE DATA · DEMO IDENTIFIER · NOT FOR SAFETY FACTS</Text> : null}
      {screen === 'home' ? (
        <HomeScreen onTakePhoto={takePhoto} onPickImage={pickImage} onDemo={() => runFixtureIdentifier(`demo-fixture-${Date.now()}`)} />
      ) : null}
      {screen === 'result' && result ? (
        <ResultScreen
          result={result}
          speciesById={speciesById}
          topSpecies={topSpecies}
          photoUri={photoUri}
          onIncidents={() => topSpecies && openIncidentPicker(topSpecies)}
          onAgain={() => setScreen('home')}
        />
      ) : null}
      {screen === 'incidents' && topSpecies ? (
        <IncidentScreen species={topSpecies} options={incidentOptions} onBack={() => setScreen('result')} />
      ) : null}
      {screen === 'error' ? <ErrorScreen message={error ?? 'Unknown error'} onHome={() => setScreen('home')} /> : null}
    </View>
  );
}

function HomeScreen({ onTakePhoto, onPickImage, onDemo }: { onTakePhoto: () => void; onPickImage: () => void; onDemo: () => void }) {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Wild Miami</Text>
      <Text style={styles.subtitle}>Offline-first wildlife ID skeleton for Android.</Text>
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Home / camera</Text>
        <Text style={styles.body}>Camera and gallery are wired to the Demo/FIXTURE identifier so the full result flow can be tested while the native model catches up.</Text>
        <Pressable style={styles.primaryButton} onPress={onTakePhoto}>
          <Text style={styles.primaryText}>Take photo</Text>
        </Pressable>
        <Pressable style={styles.secondaryButton} onPress={onPickImage}>
          <Text style={styles.secondaryText}>Choose from gallery</Text>
        </Pressable>
        <Pressable style={styles.secondaryButton} onPress={onDemo}>
          <Text style={styles.secondaryText}>Run Demo/FIXTURE identifier</Text>
        </Pressable>
      </View>
      <Text style={styles.footer}>Labels are qualitative: likely, possible, or unsure. Scores are not probabilities.</Text>
    </ScrollView>
  );
}

function ResultScreen({
  result,
  speciesById,
  topSpecies,
  photoUri,
  onIncidents,
  onAgain,
}: {
  result: Result;
  speciesById: Map<number, Species>;
  topSpecies: Species | null | undefined;
  photoUri: string | null;
  onIncidents: () => void;
  onAgain: () => void;
}) {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.kicker}>Result</Text>
      <Text style={styles.title}>{verdictTitle(result.verdict)}</Text>
      {photoUri ? <Image source={{ uri: photoUri }} style={styles.preview} /> : null}
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Top 3 alternatives</Text>
        {result.matches.map((match, index) => {
          const item = speciesById.get(match.speciesId);
          return (
            <Text key={match.speciesId} style={styles.listItem}>
              {index + 1}. {item?.commonName ?? `Species ${match.speciesId}`} {index === 0 ? `· ${result.verdict}` : ''}
            </Text>
          );
        })}
      </View>
      {topSpecies ? <SafetyCard species={topSpecies} onIncidents={onIncidents} /> : null}
      <Pressable style={styles.secondaryButton} onPress={onAgain}>
        <Text style={styles.secondaryText}>Try another</Text>
      </Pressable>
    </ScrollView>
  );
}

function SafetyCard({ species, onIncidents }: { species: Species; onIncidents: () => void }) {
  return (
    <View style={styles.card}>
      <Text style={styles.sectionTitle}>Species safety card</Text>
      <Text style={styles.speciesName}>{species.commonName}</Text>
      <Text style={styles.scientific}>{species.scientificName}</Text>
      <Text style={styles.body}>{species.blurb}</Text>
      <Text style={styles.guidance}>{species.defaultGuidance}</Text>
      <Text style={styles.meta}>Status: {species.conservationStatus}</Text>
      <Text style={styles.meta}>Source: {species.sourceUrl}</Text>
      <Text style={styles.meta}>Verified: {species.verifiedAt}</Text>
      <Text style={styles.meta}>Photo: {species.photoCredit}</Text>
      <Pressable style={styles.primaryButton} onPress={onIncidents}>
        <Text style={styles.primaryText}>Open incident picker</Text>
      </Pressable>
    </View>
  );
}

function IncidentScreen({ species, options, onBack }: { species: Species; options: IncidentOption[]; onBack: () => void }) {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.kicker}>Incident picker</Text>
      <Text style={styles.title}>{species.commonName}</Text>
      <Text style={styles.body}>Hotlines only appear here, after choosing an incident option. Fixture rows must be replaced with reviewed guidance before release.</Text>
      {options.length === 0 ? <Text style={styles.card}>No verified incident options for this fixture species.</Text> : null}
      {options.map((option) => (
        <View key={option.incident} style={styles.card}>
          <Text style={styles.sectionTitle}>{option.label}</Text>
          <Text style={styles.body}>{option.guidance}</Text>
          {option.phoneNumber ? (
            <Pressable style={styles.primaryButton} onPress={() => Linking.openURL(`tel:${option.phoneNumber}`)}>
              <Text style={styles.primaryText}>{option.phoneLabel}: {option.phoneNumber}</Text>
            </Pressable>
          ) : null}
        </View>
      ))}
      <Pressable style={styles.secondaryButton} onPress={onBack}>
        <Text style={styles.secondaryText}>Back to result</Text>
      </Pressable>
    </ScrollView>
  );
}

function ErrorScreen({ message, onHome }: { message: string; onHome: () => void }) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Something needs attention</Text>
      <Text style={styles.card}>{message}</Text>
      <Pressable style={styles.primaryButton} onPress={onHome}>
        <Text style={styles.primaryText}>Back home</Text>
      </Pressable>
    </View>
  );
}

function verdictTitle(verdict: Result['verdict']): string {
  if (verdict === 'likely') return 'Likely match';
  if (verdict === 'possible') return 'Possible match';
  return 'Not sure';
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#f5efe6' },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12, backgroundColor: '#f5efe6' },
  container: { padding: 20, paddingTop: 64, gap: 16 },
  fixtureBanner: { position: 'absolute', zIndex: 10, top: 0, left: 0, right: 0, padding: 10, backgroundColor: '#ffd166', color: '#3b2600', textAlign: 'center', fontWeight: '800' },
  kicker: { color: '#287271', fontWeight: '800', textTransform: 'uppercase', letterSpacing: 1 },
  title: { fontSize: 36, lineHeight: 40, fontWeight: '900', color: '#0f2a1d' },
  subtitle: { fontSize: 18, color: '#315441' },
  card: { backgroundColor: '#fffaf1', borderColor: '#e5dccb', borderWidth: 1, borderRadius: 18, padding: 16, gap: 10 },
  sectionTitle: { fontSize: 18, fontWeight: '800', color: '#0f2a1d' },
  speciesName: { fontSize: 24, fontWeight: '900', color: '#0f2a1d' },
  scientific: { fontStyle: 'italic', color: '#496454' },
  body: { fontSize: 16, lineHeight: 22, color: '#263b2d' },
  guidance: { fontSize: 16, lineHeight: 22, color: '#1c3527', fontWeight: '700' },
  listItem: { fontSize: 17, paddingVertical: 6, color: '#263b2d' },
  meta: { color: '#5f6f64', fontSize: 13 },
  muted: { color: '#5f6f64' },
  footer: { color: '#496454', fontSize: 13 },
  preview: { height: 220, borderRadius: 18, backgroundColor: '#e5dccb' },
  primaryButton: { backgroundColor: '#287271', padding: 14, borderRadius: 14, alignItems: 'center', marginTop: 8 },
  primaryText: { color: 'white', fontWeight: '900' },
  secondaryButton: { borderColor: '#287271', borderWidth: 2, padding: 14, borderRadius: 14, alignItems: 'center' },
  secondaryText: { color: '#287271', fontWeight: '900' },
});
