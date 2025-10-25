#pragma once

// C/C++
#include <cstdio>
#include <cstdlib>

// base
#include <configure.h>

// math
#include "lubksb.h"
#include "ludcmp.h"
#include "psolve.h"

#define A(i, j) a[(i) * n2 + (j)]
#define ATA(i, j) ata[(i) * n2 + (j)]
#define AUG(i, j) aug[(i) * (n2 + nact) + (j)]
#define C(i, j) c[(i) * n2 + (j)]

namespace kintera {

// Compute bitmask hash for a set of integers [0..n-1]
DISPATCH_MACRO uint64_t hash_set(const int *arr, int size, int n) {
  uint64_t mask = 0;
  for (int i = 0; i < size; i++) {
    int x = arr[i];
    if (x >= 0 && x < n) {
      mask |= (1ULL << x);
    }
  }
  return mask;
}

template <typename T>
DISPATCH_MACRO void populate_aug(T *aug, T const *ata, T const *c, int n2,
                                 int nact, int const *ct_indx) {
  // populate A^T.A (upper left block)
  for (int i = 0; i < n2; ++i) {
    for (int j = 0; j < n2; ++j) {
      AUG(i, j) = ATA(i, j);
    }
  }

  // populate C (lower left block)
  for (int i = 0; i < nact; ++i) {
    for (int j = 0; j < n2; ++j) {
      AUG(n2 + i, j) = C(ct_indx[i], j);
    }
  }

  // populate C^T (upper right block)
  for (int i = 0; i < n2; ++i) {
    for (int j = 0; j < nact; ++j) {
      AUG(i, n2 + j) = C(ct_indx[j], i);
    }
  }

  // zero (lower right block)
  for (int i = 0; i < nact; ++i) {
    for (int j = 0; j < nact; ++j) {
      AUG(n2 + i, n2 + j) = 0.0;
    }
    // add a small diagonal perturbation to improve numerical stability
    AUG(n2 + i, n2 + i) = -1e-10;
  }
}

template <typename T>
DISPATCH_MACRO void populate_rhs(T *rhs, T const *atb, T const *d, int n2,
                                 int nact, int const *ct_indx) {
  // populate A^T.b (upper part)
  for (int i = 0; i < n2; ++i) {
    rhs[i] = atb[i];
  }

  // populate d (lower part)
  for (int i = 0; i < nact; ++i) {
    rhs[n2 + i] = d[ct_indx[i]];
  }
}

/*!
 * \brief solve constrained least square problem: min ||A.x - b||, s.t. C.x <= d
 *
 * This subroutine solves the constrained least square problem using the active
 * set method based on the KKT conditions. The first `neq` rows of the
 * constraint matrix `C` are treated as equality constraints, while the
 * remaining rows are treated as inequality constraints.
 *
 * \param[in,out] b[0..n1-1]    right-hand-side vector and output. Input
 *                              dimension is n1, output dimension is n2,
 * requiring n1 >= n2
 * \param[in] a[0..n1*n2-1]     row-major input matrix, A
 * \param[in] c[0..n3*n2-1]     row-major constraint matrix, C
 * \param[in] d[0..n3-1]        right-hand-side constraint vector, d
 * \param[in] n1                number of rows in matrix A
 * \param[in] n2                number of columns in matrix A
 * \param[in] n3                number of rows in matrix C
 * \param[in] neq               number of equality constraints, 0 <= neq <= n3
 * \param[in,out] max_iter      in: maximum number of iterations to perform,
 *                              out: number of iterations actually performed
 * \param[in] work              workspace if not null, otherwise allocated
 *                              internally.
 *
 * \return 0 on success, 1 on invalid input (e.g., neq < 0 or neq > n3),
 *         2 on failure (max_iter reached without convergence).
 */
template <typename T>
DISPATCH_MACRO int leastsq_kkt(T *b, T const *a, T const *c, T const *d, int n1,
                               int n2, int n3, int neq, int *max_iter,
                               char *work = nullptr) {
  // check if n1 > 0, n2 > 0, n3 >= 0
  if (n1 <= 0 || n2 <= 0 || n3 < 0 || n1 < n2) {
    printf(
        "Error: n1 and n2 must be positive integers and n3 >= 0, n1 >= n2.\n");
    return 1;  // invalid input
  }

  // check if 0 <= neq <= n3
  if (neq < 0 || neq > n3) {
    printf("Error: neq must be non-negative.\n");
    return 1;  // invalid input
  }

  // Allocate memory for the augmented matrix and right-hand side vector
  int size = n2 + n3;
  T *aug, *ata, *atb, *rhs, *eval;
  int *ct_indx, *lu_indx, *skip_row;

  if (work == nullptr) {
    aug = (T *)malloc(size * size * sizeof(T));
    ata = (T *)malloc(n2 * n2 * sizeof(T));
    atb = (T *)malloc(n2 * sizeof(T));
    rhs = (T *)malloc(size * sizeof(T));

    // evaluation of constraints
    eval = (T *)malloc(n3 * sizeof(T));

    // index for the active set
    ct_indx = (int *)malloc(n3 * sizeof(int));

    // index array for the LU decomposition
    lu_indx = (int *)malloc(size * sizeof(int));

    // row indices to skip
    skip_row = (int *)malloc(size * sizeof(int));
  } else {
    aug = alloc_from<T>(work, size * size);
    ata = alloc_from<T>(work, n2 * n2);
    atb = alloc_from<T>(work, n2);
    rhs = alloc_from<T>(work, size);
    eval = alloc_from<T>(work, n3);
    ct_indx = alloc_from<int>(work, n3);
    lu_indx = alloc_from<int>(work, size);
    skip_row = alloc_from<int>(work, size);
  }

  // populate A^T.A
  for (int i = 0; i < n2; ++i) {
    for (int j = 0; j < n2; ++j) {
      ATA(i, j) = 0.0;
      for (int k = 0; k < n1; ++k) {
        ATA(i, j) += A(k, i) * A(k, j);
      }
    }
  }

  // populate A^T.b
  for (int i = 0; i < n2; ++i) {
    atb[i] = 0.0;
    for (int j = 0; j < n1; ++j) {
      atb[i] += A(j, i) * b[j];
    }
  }

  for (int i = 0; i < n3; ++i) {
    ct_indx[i] = i;
  }

  int nactive = neq;
  int iter = 0;

  while (iter++ < *max_iter) {
    /*printf("kkt iter = %d, nactive = %d\n", iter, nactive);
    printf("ct_indx = ");
    for (int i = 0; i < neq; ++i) {
      printf("%d ", ct_indx[i]);
    }
    printf("| ");
    for (int i = neq; i < nactive; ++i) {
      printf("%d ", ct_indx[i]);
    }
    printf("| ");
    for (int i = nactive; i < n3; ++i) {
      printf("%d ", ct_indx[i]);
    }
    printf("\n");*/
    uint64_t hash0 = hash_set(ct_indx, nactive, n3);

    populate_aug(aug, ata, c, n2, nactive, ct_indx);
    populate_rhs(rhs, atb, d, n2, nactive, ct_indx);

    // solve the KKT system
    // determine the non-zero rows
    for (int i = 0; i < n2 + nactive; ++i) {
      bool all_zero = true;
      for (int j = 0; j < n2 + nactive; ++j) {
        if (aug[i * (n2 + nactive) + j] != 0.0) {
          all_zero = false;
          break;
        }
      }
      skip_row[i] = all_zero;
      if (all_zero) rhs[i] = 0.0;
    }

    /* print aug
    printf("aug = \n");
    for (int i = 0; i < n2 + nactive; ++i) {
      for (int j = 0; j < n2 + nactive; ++j) {
        printf("%f ", aug[i * (n2 + nactive) + j]);
      }
      printf("| %f", rhs[i]);
      if (skip_row[i]) printf(" *");
      printf("\n");
    }*/

    ludcmp(aug, lu_indx, n2 + nactive, work, skip_row);
    lubksb(rhs, aug, lu_indx, n2 + nactive, skip_row);

    // evaluate the inactive constraints
    for (int i = nactive; i < n3; ++i) {
      int k = ct_indx[i];
      eval[k] = 0.;
      for (int j = 0; j < n2; ++j) {
        eval[k] += C(k, j) * rhs[j];
      }
    }

    /* print solution vector (rhs)
    printf("rhs = ");
    for (int i = 0; i < n2; ++i) {
      printf("%f ", rhs[i]);
    }
    printf("| ");
    for (int i = n2; i < n2 + nactive; ++i) {
      printf("%f ", rhs[i]);
    }
    printf("\n");*/

    // remove inactive constraints (three-way swap)
    //           mu < 0
    //           |---------------->|
    //           |<----|<----------|
    //           f     :...m       :...l
    //           |     :   |       :   |
    // | * * * | * * * * | * * * * * | x
    // |-------|---------|-----------|
    // |  EQ   |   INEQ  | INACTIVE  |
    int first = neq;
    int mid = nactive;
    int last = n3;
    while (first < mid) {
      if (rhs[n2 + first] < 0.0) {  // inactive constraint
        // swap with the last active constraint
        int tmp = ct_indx[first];
        ct_indx[first] = ct_indx[mid - 1];
        ct_indx[mid - 1] = ct_indx[last - 1];
        ct_indx[last - 1] = tmp;

        T val = rhs[n2 + first];
        rhs[n2 + first] = rhs[n2 + mid - 1];
        rhs[n2 + mid - 1] = val;
        --last;
        --mid;
      } else {
        ++first;
      }
    }

    /* print ct_indx after removing
    printf("ct_indx after removing = ");
    for (int i = 0; i < neq; ++i) {
      printf("%d ", ct_indx[i]);
    }
    printf("| ");
    for (int i = neq; i < nactive; ++i) {
      printf("%d ", ct_indx[i]);
    }
    printf("| ");
    for (int i = nactive; i < n3; ++i) {
      printf("%d ", ct_indx[i]);
    }
    printf("\n");*/

    // add back inactive constraints (two-way swap)
    //                     C.x <= d
    //                     |<----->|
    //                     f       : l
    //                     |       : |
    // | * * * | * * * * | * * * * * x * |
    // |-------|---------|---------------|
    // |  EQ   |   INEQ  |   INACTIVE    |
    while (first < last) {
      int k = ct_indx[first];
      if (eval[k] > d[k]) {
        // add the inactive constraint back to the active set
        ++first;
      } else {
        int tmp = ct_indx[first];
        ct_indx[first] = ct_indx[last - 1];
        ct_indx[last - 1] = tmp;
        --last;
      }
    }

    nactive = first;
    uint64_t hash1 = hash_set(ct_indx, nactive, n3);
    // no change in active set, we are done
    if (hash0 == hash1) break;
  }

  // copy to output vector b
  for (int i = 0; i < n2; ++i) {
    b[i] = rhs[i];
  }

  if (work == nullptr) {
    free(aug);
    free(ata);
    free(atb);
    free(rhs);
    free(eval);
    free(ct_indx);
    free(lu_indx);
  }

  if (iter >= *max_iter) {
    *max_iter = iter;
    printf("Warning: leastsq_kkt maximum number of iterations reached (%d).\n",
           *max_iter);
    return 2;  // failure to converge
  }

  *max_iter = iter;
  return 0;  // success
}

}  // namespace kintera

#undef A
#undef ATA
#undef AUG
#undef C
