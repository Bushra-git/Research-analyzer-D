-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL,
    "email" TEXT,
    "name" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Analysis" (
    "id" TEXT NOT NULL,
    "jobId" TEXT,
    "userId" TEXT,
    "paperFilename" TEXT NOT NULL,
    "extractedScore" DOUBLE PRECISION NOT NULL,
    "features" JSONB NOT NULL,
    "summary" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Analysis_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CachedRecommendation" (
    "id" TEXT NOT NULL,
    "userId" TEXT,
    "cacheKey" TEXT NOT NULL,
    "paperHash" TEXT NOT NULL,
    "preferencesHash" TEXT NOT NULL,
    "requestPayload" JSONB NOT NULL,
    "result" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expiresAt" TIMESTAMP(3),

    CONSTRAINT "CachedRecommendation_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE UNIQUE INDEX "Analysis_jobId_key" ON "Analysis"("jobId");

-- CreateIndex
CREATE INDEX "Analysis_createdAt_idx" ON "Analysis"("createdAt");

-- CreateIndex
CREATE UNIQUE INDEX "CachedRecommendation_cacheKey_key" ON "CachedRecommendation"("cacheKey");

-- CreateIndex
CREATE INDEX "CachedRecommendation_paperHash_idx" ON "CachedRecommendation"("paperHash");

-- CreateIndex
CREATE INDEX "CachedRecommendation_preferencesHash_idx" ON "CachedRecommendation"("preferencesHash");

-- AddForeignKey
ALTER TABLE "Analysis" ADD CONSTRAINT "Analysis_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CachedRecommendation" ADD CONSTRAINT "CachedRecommendation_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;