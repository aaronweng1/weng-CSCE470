import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.*;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

public class bm25 {

    private static final double k1 = 1.5;  // BM25 parameter
    private static final double b = 0.75;  // BM25 parameter

    public static void main(String[] args) throws IOException {
        String filePath = "Resume.csv";
        String targetCategory = "CHEF";
        String jobDescription = "chef culinary food preparation cooking experience";

        List<Resume> resumes = loadAndFilterResumes(filePath, targetCategory);
        if (resumes.isEmpty()) {
            System.out.println("No resumes found for the specified category: " + targetCategory);
            return;
        }

        double avgDocLength = resumes.stream()
                                     .mapToInt(resume -> resume.getResumeStr().split("\\s+").length)
                                     .average()
                                     .orElse(1.0);

        List<Resume> rankedResumes = rankResumesByBM25F(resumes, jobDescription, avgDocLength);

        System.out.println("Top Ranked Resumes:");
        for (int i = 0; i < rankedResumes.size(); i++) {
            Resume resume = rankedResumes.get(i);
            System.out.println("Rank " + (i + 1) + ": " + resume);
            System.out.println("Missing skills: " + getMissingSkills(jobDescription, resume.getResumeStr()));
        }
    }

    // Load and clean resumes from CSV file
    public static List<Resume> loadAndFilterResumes(String filePath, String category) throws IOException {
        List<Resume> resumes = new ArrayList<>();
        Pattern pattern = Pattern.compile("[^a-zA-Z0-9 ]");  // Pattern to remove special characters

        try (BufferedReader reader = new BufferedReader(new FileReader(filePath))) {
            String line;
            reader.readLine(); // Skip header
            while ((line = reader.readLine()) != null) {
                String[] columns = line.split(",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", -1);
                if (columns.length >= 4) {
                    String id = columns[0].replaceAll("^\"|\"$", "");
                    String resumeStr = columns[1].replaceAll("^\"|\"$", "");
                    resumeStr = pattern.matcher(resumeStr).replaceAll("").toLowerCase();  // Clean text
                    String resumeHtml = columns[2].replaceAll("^\"|\"$", "");
                    String resumeCategory = columns[3].replaceAll("^\"|\"$", "");

                    if (resumeCategory.equalsIgnoreCase(category)) {
                        resumes.add(new Resume(id, resumeStr, resumeHtml, resumeCategory));
                    }
                }
            }
        }
        System.out.println("Loaded " + resumes.size() + " resumes for category: " + category);
        return resumes;
    }

    // Rank resumes based on BM25F
    public static List<Resume> rankResumesByBM25F(List<Resume> resumes, String jobDescription, double avgDocLength) {
        Map<String, Integer> jobTermFreq = getTermFrequencies(jobDescription);

        for (Resume resume : resumes) {
            resume.setScore(calculateBM25FScore(resume, jobTermFreq, resumes.size(), avgDocLength, resumes));
        }

        return resumes.stream()
                      .sorted(Comparator.comparingDouble(Resume::getScore).reversed())
                      .collect(Collectors.toList());
    }

    // Calculate BM25F score for a resume
    public static double calculateBM25FScore(Resume resume, Map<String, Integer> jobTerms, int totalDocuments, double avgDocLength, List<Resume> resumes) {
        double score = 0.0;
        Map<String, Integer> resumeTerms = getTermFrequencies(resume.getResumeStr());

        for (String term : jobTerms.keySet()) {
            int termFreqInResume = resumeTerms.getOrDefault(term, 0);
            if (termFreqInResume > 0) {
                int docFreq = calculateDocumentFrequency(term, resumes);
                double idf = Math.log(1 + (totalDocuments - docFreq + 0.5) / (docFreq + 0.5));
                double termWeight = ((k1 + 1) * termFreqInResume) / (k1 * ((1 - b) + b * resume.getResumeStr().split("\\s+").length / avgDocLength) + termFreqInResume);
                score += idf * termWeight;
            }
        }
        return score;
    }

    // Get term frequencies in a document
    private static Map<String, Integer> getTermFrequencies(String text) {
        Map<String, Integer> termFreq = new HashMap<>();
        String[] terms = text.split("\\W+");
        for (String term : terms) {
            term = term.toLowerCase();
            termFreq.put(term, termFreq.getOrDefault(term, 0) + 1);
        }
        return termFreq;
    }

    // Calculate document frequency for a term
    private static int calculateDocumentFrequency(String term, List<Resume> resumes) {
        int docFreq = 0;
        for (Resume resume : resumes) {
            if (getTermFrequencies(resume.getResumeStr()).containsKey(term)) {
                docFreq++;
            }
        }
        return docFreq;
    }

    // Identify missing skills based on job description
    private static List<String> getMissingSkills(String jobDescription, String resumeStr) {
        Set<String> jobSkills = new HashSet<>(Arrays.asList(jobDescription.toLowerCase().split("\\s+")));
        Set<String> resumeSkills = new HashSet<>(Arrays.asList(resumeStr.toLowerCase().split("\\s+")));
        jobSkills.removeAll(resumeSkills);
        return new ArrayList<>(jobSkills);
    }
}

// Resume class definition
class Resume {
    private String id;
    private String resumeStr;
    private String resumeHtml;
    private String category;
    private double score;

    public Resume(String id, String resumeStr, String resumeHtml, String category) {
        this.id = id;
        this.resumeStr = resumeStr;
        this.resumeHtml = resumeHtml;
        this.category = category;
    }

    public String getResumeStr() {
        return resumeStr;
    }

    public double getScore() {
        return score;
    }

    public void setScore(double score) {
        this.score = score;
    }

    @Override
    public String toString() {
        return "Resume{" +
                "id='" + id + '\'' +
                ", category='" + category + '\'' +
                ", score=" + score +
                '}';
    }
}
