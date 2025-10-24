package com.launchableinc.ingest.commits;

public class JSFileChange {
  /** Number of lines added. */
  private int linesAdded;

  /** Number of lines removed. */
  private int linesDeleted;

  /**
   * File status marker, like 'M', 'A', 'D' that represents the operation.
   *
   * <p>"R" (rename) and "C" (copy) are special case because they are accompanied by the confidence
   * level, such as "R100".
   */
  private String status;

  /**
   * Get the old name associated with this file.
   *
   * <p>The meaning of the old name can differ depending on the semantic meaning of this patch:
   *
   * <ul>
   *   <li><i>file add</i>: always <code>/dev/null</code>
   *   <li><i>file modify</i>: always {@link #pathTo}
   *   <li><i>file delete</i>: always the file being deleted
   *   <li><i>file copy</i>: source file the copy originates from
   *   <li><i>file rename</i>: source file the rename originates from
   * </ul>
   */
  private String path;

  /**
   * Get the new name associated with this file.
   *
   * <p>The meaning of the new name can differ depending on the semantic meaning of this patch:
   *
   * <ul>
   *   <li><i>file add</i>: always the file being created
   *   <li><i>file modify</i>: always {@link #path)}
   *   <li><i>file delete</i>: always <code>/dev/null</code>
   *   <li><i>file copy</i>: destination file the copy ends up at
   *   <li><i>file rename</i>: destination file the rename ends up at
   * </ul>
   */
  private String pathTo;

  public int getLinesAdded() {
    return linesAdded;
  }

  public void setLinesAdded(int linesAdded) {
    this.linesAdded = linesAdded;
  }

  public int getLinesDeleted() {
    return linesDeleted;
  }

  public void setLinesDeleted(int linesDeleted) {
    this.linesDeleted = linesDeleted;
  }

  public String getPath() {
    return path;
  }

  public void setPath(String path) {
    this.path = path;
  }

  public String getPathTo() {
    return pathTo;
  }

  public void setPathTo(String pathTo) {
    this.pathTo = pathTo;
  }

  public String getStatus() {
    return status;
  }

  public void setStatus(String status) {
    this.status = status;
  }
}
