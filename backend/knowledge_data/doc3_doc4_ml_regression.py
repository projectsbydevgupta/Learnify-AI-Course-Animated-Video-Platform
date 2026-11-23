DOCUMENTS = [
    {
        "document": "ml_supervised_learning_theory.pdf",
        "topic": "Machine Learning",
        "section": "Supervised Learning & Empirical Risk Minimization",
        "pages": [
            {
                "page": 1,
                "text": """Introduction to Supervised Machine Learning (Classification and Regression):
Machine learning develops algorithms that discover patterns in data.
- Classification: Discrete categorical target labels Y = {0, 1, ..., 9} (e.g. USPS postal zip code digit recognition). Algorithm computes a mapping function from image space X to label set Y.
- Regression: Continuous real-valued target quantities Y = R (e.g. YouTube predicting median viewer age from video metadata).
Training set formulation: T = {(x1, y1), ..., (xN, yN)} with x_n in X and y_n in Y."""
            },
            {
                "page": 2,
                "text": """Hypothesis Space & Classifier Learning:
The classifier function h: X -> Y maps input features to predicted labels.
The learning algorithm lambda: T -> H selects optimal predictor h from hypothesis space H using training data T.
Parameterization: Frequently h_theta is governed by parameter vector theta.
A classifier defines a partition of the input data space X into decision regions X_y for each label y in Y."""
            },
            {
                "page": 3,
                "text": """Practical Aspects: Training Set Construction & Labeling:
Creating high-quality training sets requires careful annotation and preprocessing.
Crowdsourcing platforms like Amazon Mechanical Turk aggregate human labels, but noisy data requires consensus voting.
Regression formalization: The target is real-valued with a metric space (distance between ages is meaningful, unlike categorical labels)."""
            },
            {
                "page": 4,
                "text": """Empirical Risk Minimization (ERM):
When predictor h predicts h(x) and ground truth is y, we incur loss l(y, h(x)).
- Zero-One Loss for classification: l(y, h(x)) = 0 if h(x) == y else 1.
- Squared Error Loss for regression: l(y, h(x)) = (h(x) - y)^2.
Empirical Risk L_T(h) is the sample average loss over training set T:
L_T(h) = (1 / |T|) * sum_{(x, y) in T} l(y, h(x)).
ERM solves: argmin_{h in H} L_T(h)."""
            },
            {
                "page": 5,
                "text": """Generalization vs. Data Fitting:
Data fitting minimizes empirical risk on known training points.
Machine learning requires generalization: performing accurately on previously unseen data points drawn from the population.
Hyper-parameters: Parameters controlling model capacity (e.g. polynomial degree k).
Optimizing hyper-parameters directly via ERM causes trivial overfitting (setting degree k = N - 1 yields zero training loss but terrible generalization)."""
            },
            {
                "page": 6,
                "text": """Statistical Risk & Generative Data Model:
Assume samples (x, y) are drawn i.i.d. from true joint probability distribution p(x, y).
The true statistical risk is the expected loss over distribution p:
L_p(h) = E_p[l(y, h(x))].
The fundamental challenge is that data distribution p is unknown, so we must estimate generalization risk using held-out validation and test sets."""
            },
            {
                "page": 7,
                "text": """Curse of Dimensionality:
In high-dimensional feature spaces (X in R^d with d >> 1), training data becomes exponentially sparse.
A grid with 10 bins per dimension requires 10^100 cells in 100 dimensions, vastly exceeding atoms in the observable universe.
High dimensions demand strong inductive biases and regularization."""
            },
            {
                "page": 8,
                "text": """Annotation Costs & Practical Preprocessing:
Supervised learning requires large-scale annotated samples.
Automated preprocessing must be applied identically to both training and runtime inference pipelines to avoid train-test distribution skew."""
            },
            {
                "page": 9,
                "text": """Validation & Model Selection:
To tune hyper-parameters without tainting training or test sets, use a disjoint validation set V.
For each candidate hyper-parameter configuration pi, train optimal model on T, evaluate empirical validation risk L_V(h_pi), and select configuration pi* with minimal validation error."""
            },
            {
                "page": 10,
                "text": """Polynomial Degree Overfitting Case Study:
Training risk decreases monotonically as polynomial degree increases.
Validation risk reaches a minimum at the optimal degree (e.g. k = 3) and explodes upwards for overly complex models (k = 9) due to memorizing sample noise (overfitting).
Testing: Final evaluation on strictly held-out test set S gives unbiased generalization estimate."""
            },
            {
                "page": 11,
                "text": """Three-Way Dataset Splitting:
1. Training set T: Fits model weights theta.
2. Validation set V: Selects hyper-parameters pi.
3. Test set S: Unbiased measurement of statistical risk. Never touch test set during training or model tuning."""
            },
            {
                "page": 12,
                "text": """State of the Art & ImageNet Benchmark:
ILSVRC (ImageNet Large Scale Visual Recognition Challenge) with 1.4 million images across 1000 categories.
Evolution from hand-crafted features (28.2% error in 2010) to deep convolutional neural networks (AlexNet in 2012, ResNets with residual skip connections in 2015 reaching 2.3% human-level error)."""
            },
            {
                "page": 13,
                "text": """Deep Residual Learning & Vision Milestones:
Residual Networks (ResNet, He et al. 2016) enabled training ultra-deep architectures (50 to 152 layers) by propagating gradients directly through identity skip connections, preventing vanishing gradients."""
            },
            {
                "page": 14,
                "text": """K-Fold Cross Validation Algorithm:
Split training data T into K equal folds V1, ..., VK.
For each fold k, train on T \\ Vk and evaluate loss on Vk.
Average across all K folds computes low-variance risk estimate.
Leave-One-Out Cross Validation (LOOCV) sets K = N."""
            },
            {
                "page": 15,
                "text": """Choosing K in Cross Validation:
K = 5 to 10 offers the ideal compromise between computational cost and estimator variance, providing reliable hyperparameter guidance."""
            }
        ]
    },
    {
        "document": "ml_regression_stanford_cme250.pdf",
        "topic": "Machine Learning",
        "section": "Linear & Logistic Regression",
        "pages": [
            {
                "page": 1,
                "text": """CME 250 Stanford: Introduction to Machine Learning (Sherrie Wang).
Lecture 2: Linear and Logistic Regression.
Agenda: Bias-variance tradeoff, Linear regression, Ordinary Least Squares (OLS), R-squared, Multiple linear regression, Logistic regression, Classification metrics, Confusion matrix, ROC curves."""
            },
            {
                "page": 2,
                "text": """Supervised Learning Categories:
- Quantitative predictions -> Regression (e.g. sales, price, housing value).
- Qualitative categorical predictions -> Classification (e.g. default vs non-default, spam vs ham)."""
            },
            {
                "page": 3,
                "text": """Assessing Model Performance:
Key goal: How well does the model generalize to previously unseen data?
High training performance is meaningless without low test error."""
            },
            {
                "page": 4,
                "text": """Model Flexibility vs Error Curves:
As model flexibility increases, training Mean Squared Error (MSE) monotonically decreases.
However, test MSE follows a U-shaped curve: decreases initially as bias drops, reaches optimal flexibility, and then surges upward as variance causes overfitting."""
            },
            {
                "page": 5,
                "text": """Bias-Variance Tradeoff Decomposition:
Expected Test Error = Variance(f_hat(x)) + [Bias(f_hat(x))]^2 + Var(epsilon).
- Bias: Error from erroneous simplifying model assumptions. Simple linear models have high bias.
- Variance: Error from sensitivity to small fluctuations in training set. Complex flexible models have high variance.
- Irreducible error Var(epsilon): Intrinsic noise in data."""
            },
            {
                "page": 6,
                "text": """Simple Linear Regression Model:
Formulation: Y = beta_0 + beta_1 * X + epsilon.
beta_0 is the intercept, beta_1 is the slope.
Predicted values: y_hat = beta_0_hat + beta_1_hat * x.
Residual for the i-th observation: e_i = y_i - y_hat_i."""
            },
            {
                "page": 7,
                "text": """Least Squares Fitting & Normal Equations:
Residual Sum of Squares (RSS):
RSS = sum_{i=1}^n (y_i - y_hat_i)^2 = sum_{i=1}^n (y_i - beta_0 - beta_1 * x_i)^2.
Minimizing RSS via calculus setting partial derivatives to 0:
beta_1_hat = sum((x_i - x_bar) * (y_i - y_bar)) / sum((x_i - x_bar)^2).
beta_0_hat = y_bar - beta_1_hat * x_bar."""
            },
            {
                "page": 8,
                "text": """Measuring Goodness of Fit in Linear Regression:
1. Residual Standard Error (RSE):
RSE = sqrt( (1 / (n - 2)) * RSS ). Measures typical deviation between observed responses and regression line.
2. R-squared (Coefficient of Determination):
R^2 = 1 - (RSS / TSS) where TSS = sum (y_i - y_bar)^2 (Total Sum of Squares).
R^2 measures the proportion of variability in Y explained by predictors X (between 0 and 1)."""
            },
            {
                "page": 9,
                "text": """Multiple Linear Regression:
Y = beta_0 + beta_1 * X_1 + beta_2 * X_2 + ... + beta_p * X_p + epsilon.
Matrix Formulation:
Y = X * beta + epsilon.
Ordinary Least Squares analytical normal equations solution:
beta_hat = (X^T * X)^(-1) * X^T * Y."""
            },
            {
                "page": 10,
                "text": """Linear Regression Diagnostics & Edge Cases:
- Non-linearity of relationships (diagnosed via residual plots vs fitted values; resolved via polynomial terms X^2).
- Non-constant variance of errors / Heteroscedasticity (funnel shape in residuals; resolved via log transforms).
- Outliers and high-leverage points (disproportionately shift beta coefficients).
- Collinearity among predictors."""
            },
            {
                "page": 11,
                "text": """Scikit-Learn Implementation of Linear Regression:
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
linreg = LinearRegression()
linreg.fit(X_train, y_train)
y_pred = linreg.predict(X_test)
r2 = r2_score(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)"""
            },
            {
                "page": 12,
                "text": """Logistic Regression for Binary Classification:
Target Y in {0, 1}.
Linear regression outputs values outside [0, 1], making it invalid for probabilities.
Logistic regression models probability using the Sigmoid (Logistic) link function:
p(X) = P(Y = 1 | X) = sigma(beta_0 + beta_1 * X) = 1 / (1 + e^(-(beta_0 + beta_1 * X))).
Odds = p(X) / (1 - p(X)) = e^(beta_0 + beta_1 * X).
Log-Odds (Logit): ln(p(X) / (1 - p(X))) = beta_0 + beta_1 * X."""
            },
            {
                "page": 13,
                "text": """Maximum Likelihood Estimation (MLE) in Logistic Regression:
No closed-form analytical solution exists for logistic coefficients.
Parameters are estimated iteratively using Maximum Likelihood Estimation via Gradient Ascent / Newton-Raphson to maximize:
L(beta) = prod_{i: y_i=1} p(x_i) * prod_{j: y_j=0} (1 - p(x_j))."""
            },
            {
                "page": 14,
                "text": """Evaluating Classification Models - Confusion Matrix:
- True Positive (TP): Ground truth 1, predicted 1.
- False Positive (FP): Ground truth 0, predicted 1 (Type I error).
- False Negative (FN): Ground truth 1, predicted 0 (Type II error).
- True Negative (TN): Ground truth 0, predicted 0.
Metrics:
Accuracy = (TP + TN) / Total.
Precision = TP / (TP + FP).
Recall (Sensitivity) = TP / (TP + FN).
Specificity = TN / (TN + FP).
False Positive Rate (FPR) = FP / (FP + TN) = 1 - Specificity."""
            },
            {
                "page": 15,
                "text": """ROC Curves & Scikit-Learn Classification:
Receiver Operating Characteristic (ROC) curve plots True Positive Rate (Sensitivity) vs False Positive Rate (1 - Specificity) across all decision thresholds.
AUC (Area Under Curve) aggregates performance: AUC = 1.0 is a perfect classifier, AUC = 0.5 is random guessing.
Scikit-Learn:
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, roc_auc_score
logreg = LogisticRegression()
logreg.fit(X_train, y_train)
y_pred = logreg.predict(X_test)"""
            }
        ]
    }
]
